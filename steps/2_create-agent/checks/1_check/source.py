import json
import requests
import uuid
from azure.identity import ClientSecretCredential
from azure.ai.projects import AIProjectClient
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.core.exceptions import HttpResponseError


TARGET_MODEL = "gpt-4.1"
# A secondary purpose of this check is to assign Azure AI User to the foundry project's managed identity
AZURE_AI_USER_ROLE_DEFINITION_ID = "53ca6127-db72-4b80-b1b0-d745d6d5456d"


def with_hint(result, hint=None):
    return {
        "result": result,
        "hint_message": hint
        or "Check the Model - it should be gpt-4.1-mini and ensure throttling is set to 5k tokens per minute",
    }


def authorized_get(url, bearer_token):
    return requests.get(url, headers={"Authorization": f"Bearer {bearer_token.token}"})


def authorized_put(uri, bearer_token, additional_headers={}, data=None):
    headers = {
        "Authorization": f"Bearer {bearer_token.token}",
        "Content-Type": "application/json",
    }
    headers.update(additional_headers)
    return requests.put(uri, data=data, headers=headers)


def list_role_assignments(bearer_token, scope):
    url = f"https://management.azure.com{scope}/providers/Microsoft.Authorization/roleAssignments?api-version=2022-04-01"
    response = authorized_get(url, bearer_token)
    return response.json()["value"]


def create_role_assignment(bearer_token, scope, fq_role_definition_id, principal_id):
    role_assignment_name = str(uuid.uuid4())
    url = f"https://management.azure.com{scope}/providers/Microsoft.Authorization/roleAssignments/{role_assignment_name}?api-version=2022-04-01"
    data = json.dumps(
        {
            "properties": {
                "roleDefinitionId": fq_role_definition_id,
                "principalId": principal_id,
                "principalType": "ServicePrincipal",
            }
        }
    )
    response = authorized_put(url, bearer_token, data=data)
    return response.json()


def assign_role_to_managed_identity(
    credentials, subscription_id, role_definition_id, project_account
):
    # No auhthorization client in in lambda layer, so using REST API calls
    managed_identity_principal_id = project_account.identity.principal_id
    role_def_id = f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{AZURE_AI_USER_ROLE_DEFINITION_ID}"
    scope = project_account.id  # resource ID of the foundry project account
    bearer_token = credentials.get_token("https://management.azure.com/.default")

    # Idempotent check: is there already an assignment for this principal+role?
    existing = [
        ra
        for ra in list_role_assignments(bearer_token, scope)
        if ra["properties"]["principalId"] == managed_identity_principal_id
        and ra["properties"]["roleDefinitionId"].lower() == role_def_id.lower()
    ]
    if existing:
        return

    fq_role_definition_id = f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{role_definition_id}"
    create_role_assignment(
        bearer_token, scope, fq_role_definition_id, managed_identity_principal_id
    )


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

    assign_role_to_managed_identity(
        credentials, subscription_id, AZURE_AI_USER_ROLE_DEFINITION_ID, project_account
    )

    endpoint = project_account.properties.endpoints["AI Foundry API"]
    # Trim -resource from Foundry resource name
    project_name = project_account.name.replace("-resource", "")
    endpoint = endpoint + f"api/projects/{project_name}"
    client = AIProjectClient(
        credential=credentials, endpoint=endpoint, subscription_id=subscription_id
    )

    deployments = [
        deployment
        for deployment in client.deployments.list()
        if deployment.model_name == TARGET_MODEL
    ]
    if len(deployments) == 0:
        return with_hint(False, "Did you create the Foundry AI Agent?")

    return True


def get_credentials(event):
    subscription_id = event["environment_params"]["subscription_id"]
    credentials = ClientSecretCredential(
        client_id=event["credentials"]["credential_id"],
        client_secret=event["credentials"]["credential_key"],
        tenant_id=event["environment_params"]["tenant"],
    )
    return credentials, subscription_id
