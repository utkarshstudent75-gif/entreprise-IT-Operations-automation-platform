# Managed Identity Module

This module provisions an Azure User Assigned Managed Identity.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the user assigned managed identity. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the user assigned managed identity. | n/a | yes |
| `location` | `string` | The Azure region where the user assigned managed identity will be created. | n/a | yes |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `identity_id` | The ID of the user assigned managed identity. |
| `identity_name` | The name of the user assigned managed identity. |
| `principal_id` | The Principal ID associated with this Managed Service Identity. |
| `client_id` | The Client ID associated with this Managed Service Identity. |
| `location` | The location of the user assigned managed identity. |
