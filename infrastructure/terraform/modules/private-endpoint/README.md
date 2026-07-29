# Private Endpoint Module

This module provisions a reusable Private Endpoint in Azure.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the private endpoint. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the private endpoint. | n/a | yes |
| `location` | `string` | The Azure region where the private endpoint will be created. | n/a | yes |
| `subnet_id` | `string` | The ID of the subnet where the private endpoint should be created. | n/a | yes |
| `private_connection_resource_id` | `string` | The ID of the target resource for the private link service. | n/a | yes |
| `subresource_names` | `list(string)` | A list of subresources association (e.g. vault, blob, registry, postgresqlServer, redisCache). | n/a | yes |
| `private_dns_zone_ids` | `list(string)` | A list of Private DNS Zone IDs to link with the Private Endpoint. | `[]` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `private_endpoint_id` | The ID of the private endpoint. |
| `private_endpoint_name` | The name of the private endpoint. |
| `private_ip_address` | The private IP address of the endpoint. |
| `location` | The location of the private endpoint. |
