# Application Insights Module

This module provisions an Azure Application Insights instance linked to a central Log Analytics Workspace.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the Application Insights resource. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the Application Insights resource. | n/a | yes |
| `location` | `string` | The Azure region where the Application Insights resource will be created. | n/a | yes |
| `workspace_id` | `string` | The Resource ID of the Log Analytics Workspace to link this Application Insights resource with. | n/a | yes |
| `application_type` | `string` | Specifies the type of Application Insights to create. | `web` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `app_insights_id` | The ID of the Application Insights resource. |
| `app_insights_name` | The name of the Application Insights resource. |
| `instrumentation_key` | The Instrumentation Key of the Application Insights resource. |
| `connection_string` | The Connection String of the Application Insights resource. |
| `location` | The location of the Application Insights resource. |
