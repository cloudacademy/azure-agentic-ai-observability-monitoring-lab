# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=4.80.0"
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

variable "resource_group_name" {
  # The value of this variable will be set once launched plan / apply
  # comment this before adding it to lab

}

data "azurerm_resource_group" "current" {
  name = var.resource_group_name
}

data "azurerm_subscription" "current" {}

resource "random_id" "suffix" {
  byte_length = 6
}

locals {
  azure_ai_name = "qa-ai-${lower(random_id.suffix.hex)}"
  lab_location  = "southcentralus"
  project_name  = "qa-proj-${lower(random_id.suffix.hex)}"
}

resource "azurerm_cognitive_account" "airesource" {
  name                = local.azure_ai_name
  location            = local.lab_location
  resource_group_name = data.azurerm_resource_group.current.name
  kind                = "AIServices"

  sku_name                   = "S0"
  custom_subdomain_name      = local.azure_ai_name
  local_auth_enabled         = false
  project_management_enabled = true

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_cognitive_account_project" "project" {
  name                 = local.project_name
  cognitive_account_id = azurerm_cognitive_account.airesource.id
  location             = local.lab_location
  display_name         = "Lab Project"
  description          = "Default lab project for Microsoft Foundry."

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_cognitive_deployment" "chat_model" {
  name                 = "chat-model"
  cognitive_account_id = azurerm_cognitive_account.airesource.id

  model {
    format  = "OpenAI"
    name    = "gpt-5-nano"
    version = "2025-08-07"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 1
  }
}

resource "azurerm_role_assignment" "project_identity_foundry_user" {
  scope              = azurerm_cognitive_account.airesource.id
  role_definition_id = "${data.azurerm_subscription.current.id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
  principal_id       = azurerm_cognitive_account_project.project.identity[0].principal_id
}

resource "azurerm_role_assignment" "ai_account_identity_foundry_user" {
  scope              = azurerm_cognitive_account.airesource.id
  role_definition_id = "${data.azurerm_subscription.current.id}/providers/Microsoft.Authorization/roleDefinitions/53ca6127-db72-4b80-b1b0-d745d6d5456d"
  principal_id       = azurerm_cognitive_account.airesource.identity[0].principal_id
}

resource "azurerm_log_analytics_workspace" "observability" {
  name                = "logs-${lower(random_id.suffix.hex)}"
  location            = local.lab_location
  resource_group_name = data.azurerm_resource_group.current.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 0.05
}

resource "azurerm_application_insights" "observability" {
  name                = "insights-${lower(random_id.suffix.hex)}"
  location            = local.lab_location
  resource_group_name = data.azurerm_resource_group.current.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.observability.id

  local_authentication_enabled = true
}

resource "azurerm_role_assignment" "project_identity_application_insights_reader" {
  scope                = azurerm_application_insights.observability.id
  role_definition_name = "Reader"
  principal_id         = azurerm_cognitive_account_project.project.identity[0].principal_id
}

resource "azurerm_role_assignment" "project_identity_application_insights_metrics_publisher" {
  scope                = azurerm_application_insights.observability.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azurerm_cognitive_account_project.project.identity[0].principal_id
}

resource "azurerm_role_assignment" "project_identity_log_analytics_reader" {
  scope                = azurerm_log_analytics_workspace.observability.id
  role_definition_name = "Log Analytics Reader"
  principal_id         = azurerm_cognitive_account_project.project.identity[0].principal_id
}
