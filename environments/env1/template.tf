# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.92.0"
    }
    azapi = {
      source = "azure/azapi"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}


# Configure the Microsoft Azure Provider
provider "azapi" {
}

variable "resource_group_name" {
  # The value of this variable will be set once launched plan / apply
  # comment this before adding it to lab

}

data "azurerm_resource_group" "current" {
  name = var.resource_group_name
}

data "azurerm_client_config" "current" {
}

// STORAGE ACCOUNT
resource "azurerm_storage_account" "default" {
  name                     = "tf${lower(random_id.storage_account.hex)}"
  location                 = data.azurerm_resource_group.current.location
  resource_group_name      = data.azurerm_resource_group.current.name
  account_tier             = "Standard"
  account_replication_type = "GRS"
}

// KEY VAULT
resource "azurerm_key_vault" "default" {
  name                       = "${var.prefix}keyva-${lower(random_id.suffix.hex)}"
  location                   = data.azurerm_resource_group.current.location
  resource_group_name        = data.azurerm_resource_group.current.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  soft_delete_retention_days = 10
}

// AzAPI AIServices
resource "azapi_resource" "AIServicesResource" {
  type      = "Microsoft.CognitiveServices/accounts@2023-10-01-preview"
  name      = "AISerRes${lower(random_id.suffix.hex)}"
  location  = "eastus"
  parent_id = data.azurerm_resource_group.current.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    name = "AISerRes${lower(random_id.suffix.hex)}"
    properties = {
      //restore = true
      customSubDomainName = random_string.this.result
    }
    kind = "AIServices"
    sku = {
      name = var.sku
    }
  }

  response_export_values = ["*"]
}

// Azure AI Hub
resource "azapi_resource" "hub" {
  type      = "Microsoft.MachineLearningServices/workspaces@2024-04-01-preview"
  name      = "hub-${lower(random_id.suffix.hex)}-aih"
  location  = data.azurerm_resource_group.current.location
  parent_id = data.azurerm_resource_group.current.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      #description    = "This is QA Lab AI hub"
      friendlyName   = "lab-ai-hub"
      storageAccount = azurerm_storage_account.default.id
      keyVault       = azurerm_key_vault.default.id
    }
    kind = "hub"
  }
}

// Azure AI Project
resource "azapi_resource" "project" {
  type      = "Microsoft.MachineLearningServices/workspaces@2024-04-01-preview"
  name      = "ai-proj-${lower(random_id.suffix.hex)}"
  location  = data.azurerm_resource_group.current.location
  parent_id = data.azurerm_resource_group.current.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {
      #description   = "This is Azure AI PROJECT"
      friendlyName  = "lab-ai-project"
      hubResourceId = azapi_resource.hub.id
    }
    kind = "project"
  }
}

// AzAPI AI Services Connection
resource "azapi_resource" "AIServicesConnection" {
  type      = "Microsoft.MachineLearningServices/workspaces/connections@2024-04-01-preview"
  name      = "Default_AIServices${lower(random_id.suffix.hex)}"
  parent_id = azapi_resource.hub.id

  body = {
    properties = {
      category      = "AIServices",
      target        = azapi_resource.AIServicesResource.output.properties.endpoint,
      authType      = "AAD",
      isSharedToAll = true,
      metadata = {
        ApiType    = "Azure",
        ResourceId = azapi_resource.AIServicesResource.id
      }
    }
  }
  response_export_values = ["*"]
}
resource "random_id" "storage_account" {
  byte_length = 6
}

resource "random_string" "this" {
  length  = 8
  special = false
  upper   = false
}

resource "random_id" "suffix" {
  byte_length = 6
}

resource "azurerm_cognitive_deployment" "gpt-35-model" {
  name                 = "gpt-4.1-mini-model"
  cognitive_account_id = azapi_resource.AIServicesResource.id
  model {
    format = "OpenAI"
    name   = "gpt-4.1-mini"
  }
  scale {
    type     = "GlobalStandard"
    capacity = 5
  }
}

resource "azurerm_cognitive_deployment" "gpt-4o-model" {
  name                 = "gpt-4o-model"
  cognitive_account_id = azapi_resource.AIServicesResource.id
  model {
    format = "OpenAI"
    name   = "gpt-4o"
  }
  scale {
    type     = "Standard"
    capacity = 5
  }
}
variable "prefix" {
  type        = string
  description = "This variable is used to name the hub, project, and dependent resources."
  default     = "ai-"
}
variable "sku" {
  type        = string
  description = "The sku name of the Azure Analysis Services server to create."
  default     = "S0"
}

resource "azurerm_role_assignment" "ml_contributor_user" {
  scope                = azapi_resource.AIServicesResource.id
  role_definition_name = "Azure AI Developer"
  principal_id         = azapi_resource.hub.output.identity.principalId
}

resource "azurerm_log_analytics_workspace" "observability" {
  name                = "logs-${lower(random_id.suffix.hex)}"
  location            = data.azurerm_resource_group.current.location
  resource_group_name = data.azurerm_resource_group.current.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "observability" {
  name                = "insights-${lower(random_id.suffix.hex)}"
  location            = data.azurerm_resource_group.current.location
  resource_group_name = data.azurerm_resource_group.current.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.observability.id
}