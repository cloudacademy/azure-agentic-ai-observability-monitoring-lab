### Introduction

In this lab step, you will explore the Azure Resource Group that was created as part of the lab environment setup. This resource group contains all the necessary resources for building, deploying, and monitoring AI agents using Microsoft Foundry Agent Service, Application Insights, and Log Analytics.

You will also create a new project in the Foundry portal, which will serve as the foundation for building your AI agent in subsequent steps.

### Instructions

1. In the Azure portal, enter *resource groups* in the search bar and select *Resource groups* from the results:

    ![](assets/20251223165349.png){: style="width:150px"}

1. Click the resource group created for this lab, *cal-####-###*:

    ![](assets/20251223165432.png){: style="width:111px"}

    This lab will touch on several resources within this resource group, including the Microsoft Foundry Agent Service, Application Insights, and Log Analytics workspace:

    ![](assets/20251223165756.png){: style="width:580px"}

    - Microsoft Foundry Agent Service (Foundry): This service allows you to create and manage AI agents that can interact with users and other services. The Foundry portal provides tools for building, deploying, and monitoring these agents.
    - Log Analytics Workspace: The centralized repository for collecting and analyzing log data from various sources, including your AI agents. It enables you to perform advanced queries and create visualizations to gain insights into your agents' behavior.
    - Application Insights: The application performance management service that provides insights into the performance and usage of your AI agents. Application Insights stores its telemetry in a connected Log Analytics workspace, letting you query, correlate, and visualize AI agent performance data with Kusto-based analytics.

1. Click the **AISerRes###** Foundry resource:

    ![](assets/20251223170411.png){: style="width:491px"}

1. Click **Go to Foundry portal** to open the Microsoft Foundry portal in a new tab:

    ![](assets/20251223170508.png){: style="width:172px"}

1. Click the **New Foundry** toggle button to switch the new Foundry portal experience:

    ![](assets/20251223170634.png){: style="width:140px"}

    You will be prompted to select or create a project.

1. Select **Create a new project** from the dropdown menu:

    ![](assets/20251223170725.png){: style="width:616px"}

1. In the **Create a project** pane, enter *qa-project-###* below **Project**, replacing *###* with a unique number.

1. Select the **cal-####** resource group from the **Resource group** dropdown menu, then click **Create**:

    ![](assets/20251229144037.png){: style="width:613px"}

    Leave all other settings at their defaults. The project setup will take up to 2 minutes to complete.

    Once completed, the Foundry portal will display the project dashboard:

    ![](assets/20251229144301.png){: style="width:1030px"}

### Summary

In this lab step, you reviewed the Azure Resource Group created for the lab environment and created a new project in the Microsoft Foundry portal.