# Private DNS Module

This module provisions Private DNS Zones in Azure and links them to a target Virtual Network (VNet).

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `resource_group_name` | `string` | The name of the resource group in which to create the private DNS zones. | n/a | yes |
| `vnet_id` | `string` | The ID of the virtual network to link the Private DNS zones to. | n/a | yes |
| `private_dns_zones` | `list(string)` | A list of Private DNS zone names to create. | `[...]` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resources. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `private_dns_zone_ids` | A map of Private DNS zone names to their resource IDs. |
| `private_dns_zone_names` | A list of Private DNS zone names. |
