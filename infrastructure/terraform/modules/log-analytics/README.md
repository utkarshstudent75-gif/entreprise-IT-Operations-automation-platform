# Log Analytics Workspace Module

This module provisions a central Azure Log Analytics Workspace for storing application logs, resource diagnostics, and operational metrics.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the Log Analytics Workspace. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the Log Analytics Workspace. | n/a | yes |
| `location` | `string` | The Azure region where the Log Analytics Workspace will be created. | n/a | yes |
| `retention_in_days` | `number` | The data retention in days (min 30). | `30` | no |
| `sku` | `string` | Specifies the SKU of the workspace. | `PerGB2018` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `workspace_id` | The Resource ID of the Log Analytics Workspace. |
| `workspace_workspace_id` | The Workspace ID (client ID) of the Log Analytics Workspace. |
| `workspace_name` | The name of the Log Analytics Workspace. |
| `location` | The location of the Log Analytics Workspace. |
