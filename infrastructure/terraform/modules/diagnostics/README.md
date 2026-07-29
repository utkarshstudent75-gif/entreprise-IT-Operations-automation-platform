# Diagnostics Module

This module provisions an Azure Monitor Diagnostic Setting to route logs and metrics of a target resource to a central Log Analytics Workspace.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the diagnostic setting. | n/a | yes |
| `target_resource_id` | `string` | The ID of the target resource. | n/a | yes |
| `log_analytics_workspace_id` | `string` | The ID of the Log Analytics Workspace where diagnostics data should be sent. | n/a | yes |
| `log_categories` | `list(string)` | A list of log categories to enable. | `[]` | no |
| `metric_categories` | `list(string)` | A list of metric categories to enable. | `["AllMetrics"]` | no |

## Outputs

| Name | Description |
|------|-------------|
| `diagnostic_setting_id` | The ID of the Diagnostic Setting. |
