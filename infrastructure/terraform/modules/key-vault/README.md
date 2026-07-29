# Key Vault Module

This module provisions an Azure Key Vault with soft-delete, purge protection, and Azure RBAC authorization enabled.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the Key Vault. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the Key Vault. | n/a | yes |
| `location` | `string` | The Azure region where the Key Vault will be created. | n/a | yes |
| `tenant_id` | `string` | The Microsoft Entra ID tenant ID that should be used for authorizing requests to this Key Vault. | n/a | yes |
| `sku_name` | `string` | The SKU name of the Key Vault (standard or premium). | `standard` | no |
| `soft_delete_retention_days` | `number` | The number of days that items should be retained for once soft-deleted. | `7` | no |
| `purge_protection_enabled` | `bool` | Is Purge Protection enabled for this Key Vault? | `true` | no |
| `enable_rbac_authorization` | `bool` | Boolean flag to specify whether Azure Key Vault uses Role Based Access Control (RBAC) for authorization. | `true` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `key_vault_id` | The ID of the Key Vault. |
| `key_vault_name` | The name of the Key Vault. |
| `key_vault_uri` | The URI of the Key Vault. |
| `location` | The location of the Key Vault. |
