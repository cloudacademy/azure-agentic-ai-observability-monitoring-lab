import requests
from azure.identity import ClientSecretCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient


FAILURE_HINT = (
    "Did you connect Application Insights to the Foundry project and use the agent?"
)


def with_hint(result, hint=None):
    return {
        "result": result,
        "hint_message": hint or FAILURE_HINT,
    }


def failure():
    return with_hint(False)


def authorized_get(credentials, url):
    bearer_token = credentials.get_token("https://management.azure.com/.default")
    response = requests.get(url, headers={"Authorization": f"Bearer {bearer_token.token}"})
    response.raise_for_status()
    return response.json()


def list_resources_by_type(credentials, subscription_id, resource_group, resource_type):
    url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}/resources"
        "?api-version=2021-04-01"
        f"&$filter=resourceType eq '{resource_type}'"
    )
    return authorized_get(credentials, url).get("value", [])


def get_resource_details(credentials, resource_id, api_versions):
    for api_version in api_versions:
        url = f"https://management.azure.com{resource_id}?api-version={api_version}"
        try:
            return authorized_get(credentials, url)
        except Exception:
            continue

    raise RuntimeError("Unable to read resource details")


def get_foundry_projects(credentials, subscription_id, resource_group, account_id):
    resources = list_resources_by_type(
        credentials,
        subscription_id,
        resource_group,
        "Microsoft.CognitiveServices/accounts/projects",
    )
    account_project_prefix = f"{account_id}/projects/".lower()
    return [
        resource
        for resource in resources
        if resource.get("id", "").lower().startswith(account_project_prefix)
    ]


def list_application_insights(credentials, subscription_id, resource_group):
    return list_resources_by_type(
        credentials,
        subscription_id,
        resource_group,
        "Microsoft.Insights/components",
    )


def get_workspace_resource_id(credentials, app_insights):
    details = get_resource_details(
        credentials,
        app_insights["id"],
        ["2020-02-02", "2018-05-01-preview", "2015-05-01"],
    )
    workspace_id = details.get("properties", {}).get("WorkspaceResourceId")
    if not workspace_id:
        raise RuntimeError("Application Insights has no WorkspaceResourceId")
    return workspace_id


def get_workspace_customer_id(credentials, workspace_resource_id):
    details = get_resource_details(
        credentials,
        workspace_resource_id,
        ["2023-09-01", "2022-10-01", "2021-12-01-preview", "2020-08-01"],
    )
    customer_id = details.get("properties", {}).get("customerId")
    if not customer_id:
        raise RuntimeError("Log Analytics workspace has no customerId")
    return customer_id


def query_workspace(credentials, workspace_customer_id):
    token = credentials.get_token("https://api.loganalytics.io/.default")
    url = f"https://api.loganalytics.io/v1/workspaces/{workspace_customer_id}/query"
    query = """
let Lookback = 2h;
let RecentTelemetry =
    union isfuzzy=true AppTraces, AppRequests, AppDependencies, AppEvents
    | where TimeGenerated > ago(Lookback)
    | extend searchable = tostring(pack_all());
RecentTelemetry
| summarize
    TotalTelemetry=count(),
    AgentSignals=countif(searchable has_any (
        "agent",
        "conversation",
        "response",
        "Foundry",
        "Azure AI",
        "ai.azure.com"
    ))
"""
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json",
        },
        json={"query": query, "timespan": "PT2H"},
    )
    response.raise_for_status()
    return response.json()


def get_query_counts(query_result):
    tables = query_result.get("tables", [])
    if not tables:
        return 0, 0

    rows = tables[0].get("rows", [])
    if not rows:
        return 0, 0

    try:
        return int(rows[0][0]), int(rows[0][1])
    except Exception:
        return 0, 0


def handler(event, context):
    try:
        credentials, subscription_id = get_credentials(event)
        resource_group = event["environment_params"]["resource_group"]
    except Exception:
        return failure()

    try:
        mgmt_client = CognitiveServicesManagementClient(credentials, subscription_id)
        accounts = list(mgmt_client.accounts.list_by_resource_group(resource_group))
    except Exception:
        return failure()

    project_account = None
    for account in accounts:
        if account.kind.lower() == "aiservices":
            project_account = account
            break

    if not project_account:
        return failure()

    try:
        projects = get_foundry_projects(
            credentials, subscription_id, resource_group, project_account.id
        )
    except Exception:
        return failure()

    if len(projects) == 0:
        return failure()

    try:
        application_insights = list_application_insights(
            credentials, subscription_id, resource_group
        )
    except Exception:
        return failure()

    if len(application_insights) == 0:
        return failure()

    for component in application_insights:
        try:
            workspace_resource_id = get_workspace_resource_id(credentials, component)
            workspace_customer_id = get_workspace_customer_id(
                credentials, workspace_resource_id
            )
            query_result = query_workspace(credentials, workspace_customer_id)
            telemetry_count, signal_count = get_query_counts(query_result)
        except Exception:
            continue

        if telemetry_count > 0:
            return with_hint(
                True,
                f"Found Application Insights telemetry in {component.get('name')}: "
                f"{telemetry_count} records in the last 2 hours, "
                f"including {signal_count} agent-like records.",
            )

    return failure()


def get_credentials(event):
    subscription_id = event["environment_params"]["subscription_id"]
    credentials = ClientSecretCredential(
        client_id=event["credentials"]["credential_id"],
        client_secret=event["credentials"]["credential_key"],
        tenant_id=event["environment_params"]["tenant"],
    )
    return credentials, subscription_id
