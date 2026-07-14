import requests
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient


FAILURE_HINT = "Did you connect Application Insights to the Foundry project?"


def with_hint(result, hint=None):
    return {
        "result": result,
        "hint_message": hint or FAILURE_HINT,
    }


def failure():
    return with_hint(False)


def authorized_get(credentials, url):
    token = credentials.get_token("https://management.azure.com/.default")
    response = requests.get(url, headers={"Authorization": f"Bearer {token.token}"})
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


def get_foundry_projects(credentials, subscription_id, resource_group, account_id):
    resources = list_resources_by_type(
        credentials,
        subscription_id,
        resource_group,
        "Microsoft.CognitiveServices/accounts/projects",
    )
    project_prefix = f"{account_id}/projects/".lower()
    return [
        resource
        for resource in resources
        if resource.get("id", "").lower().startswith(project_prefix)
    ]


def list_application_insights(credentials, subscription_id, resource_group):
    return list_resources_by_type(
        credentials,
        subscription_id,
        resource_group,
        "Microsoft.Insights/components",
    )


def list_foundry_connections(credentials, subscription_id, endpoint):
    client = AIProjectClient(
        credential=credentials, endpoint=endpoint, subscription_id=subscription_id
    )
    return list(client.connections.list())


def connection_matches_app_insights(connection, app_insights_resources):
    text = str(connection).lower()
    app_insights_markers = (
        "appinsights",
        "applicationinsights",
        "app insights",
        "microsoft.insights/components",
    )

    for component in app_insights_resources:
        component_id = component.get("id", "").lower()
        component_name = component.get("name", "").lower()
        if component_id and component_id in text:
            return True
        if component_name and component_name in text:
            return True

    return any(marker in text for marker in app_insights_markers)


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

    foundry_account = next(
        (account for account in accounts if account.kind.lower() == "aiservices"),
        None,
    )
    if not foundry_account:
        return failure()

    try:
        projects = get_foundry_projects(
            credentials, subscription_id, resource_group, foundry_account.id
        )
    except Exception:
        return failure()

    if not projects:
        return failure()

    try:
        app_insights_resources = list_application_insights(
            credentials, subscription_id, resource_group
        )
    except Exception:
        return failure()

    if not app_insights_resources:
        return failure()

    base_endpoint = foundry_account.properties.endpoints["AI Foundry API"]
    for project in projects:
        project_name = project["id"].split("/projects/", 1)[1]
        endpoint = base_endpoint + f"api/projects/{project_name}"
        try:
            connections = list_foundry_connections(credentials, subscription_id, endpoint)
        except Exception:
            continue

        matching_connections = [
            connection
            for connection in connections
            if connection_matches_app_insights(connection, app_insights_resources)
        ]
        if matching_connections:
            names = [
                str(getattr(connection, "name", "unknown"))
                for connection in matching_connections
            ]
            return with_hint(
                True,
                f"Found Application Insights connection on project {project_name}: "
                f"{', '.join(names)}.",
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
