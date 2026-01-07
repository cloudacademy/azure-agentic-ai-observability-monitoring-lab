# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.92.0"
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

resource "random_id" "suffix" {
  byte_length = 6
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
