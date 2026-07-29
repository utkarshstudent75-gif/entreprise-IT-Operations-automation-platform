# Container Registry Module

This module provisions an Azure Container Registry (ACR).

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the container registry. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the container registry. | n/a | yes |
| `location` | `string` | The Azure region where the container registry will be created. | n/a | yes |
| `sku` | `string` | The SKU of the container registry (e.g., Premium). | `Premium` | no |
| `admin_enabled` | `bool` | Specifies whether the admin user is enabled. | `false` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `acr_id` | The ID of the Container Registry. |
| `acr_name` | The name of the Container Registry. |
| `acr_login_server` | The URL that can be used to log into the container registry. |
| `location` | The location of the Container Registry. |
