# Storage Account Module

This module provisions an Azure Storage Account with enterprise security baselines (HTTPS-only, TLS 1.2+, and disabled public blob access).

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the storage account. Must be unique globally. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the storage account. | n/a | yes |
| `location` | `string` | The Azure region where the storage account will be created. | n/a | yes |
| `account_tier` | `string` | Defines the Tier to use for this storage account. | `Standard` | no |
| `account_replication_type` | `string` | Defines the type of replication to use. | `LRS` | no |
| `min_tls_version` | `string` | The minimum supported TLS version. | `TLS1_2` | no |
| `https_traffic_only_enabled` | `bool` | Forces HTTPS for all traffic. | `true` | no |
| `allow_nested_items_to_be_public` | `bool` | Allow public access to blobs or containers. | `false` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `storage_account_id` | The ID of the storage account. |
| `storage_account_name` | The name of the storage account. |
| `primary_blob_endpoint` | The endpoint URL for blob storage in the primary location. |
| `primary_connection_string` | The connection string associated with the primary location. |
| `location` | The location of the storage account. |
