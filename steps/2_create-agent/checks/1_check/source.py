from azure.identity import ClientSecretCredential
from azure.ai.projects import AIProjectClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.core.exceptions import HttpResponseError

TARGET_MODEL = "gpt-4.1-mini"
TARGET_CAPACITY = 5

def with_hint(result, hint=None):
    return {
        "result": result,
        "hint_message": hint or "Check the Model - it should be gpt-4.1-mini and ensure throttling is set to 5k tokens per minute",
    }

def handler(event, context):
    credentials, subscription_id = get_credentials(event)
    resource_group = event["environment_params"]["resource_group"]

    # Find the AI Foundry project
    mgmt_client = CognitiveServicesManagementClient(credentials, subscription_id)
    accounts = list(mgmt_client.accounts.list_by_resource_group(resource_group))
    
    # Look for AIServices kind account (AI Foundry hub/project)
    project_account = None
    for account in accounts:
        if account.kind == "AIServices":
            project_account = account
            break
    
    if not project_account:
        return with_hint(False, "No AI Foundry project found in resource group")
    
    endpoint = project_account.properties.endpoints['AI Foundry API']
    # Trim -resource from Foundry resource name
    project_name = project_account.name.replace("-resource", "")
    endpoint = endpoint + f"/api/projects/{project_name}"
    client = AIProjectClient(credential=credentials, endpoint=endpoint, subscription_id=subscription_id)

    agents = list(client.agents.list_agents())
    if len(agents) != 1:
        return with_hint(False, "Did you create the Foundry AI Agent?")

    agent = agents[0]
    deployment_link = agent.model if hasattr(agent, "model") else None
    if not deployment_link:
        return with_hint(False, "Agent model is not defined")

    try:
        deployment = client.deployments.get(deployment_link)
    except HttpResponseError as e:
        print(f"get deployment failed: {e.status_code} {e.message}")
        return with_hint(False, "Failed to retrieve model deployment")

    model_matches = getattr(deployment, "model_name", "") == TARGET_MODEL
    capacity = getattr(getattr(deployment, "sku", None), "capacity", None)

    if not (model_matches and capacity <= TARGET_CAPACITY):
        return with_hint(False) # enforce by policy so shouldn't happen, omitting custom hint

    return True


def get_credentials(event):
    subscription_id = event["environment_params"]["subscription_id"]
    credentials = ClientSecretCredential(
        client_id=event["credentials"]["credential_id"],
        client_secret=event["credentials"]["credential_key"],
        tenant_id=event["environment_params"]["tenant"],
    )
    return credentials, subscription_id
