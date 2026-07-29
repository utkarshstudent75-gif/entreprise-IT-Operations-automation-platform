# Virtual Network Module

This module provisions an Azure Virtual Network (VNet).

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `resource_group_name` | `string` | The name of the resource group in which to create the virtual network. | n/a | yes |
| `location` | `string` | The Azure region where the virtual network will be created. | n/a | yes |
| `vnet_name` | `string` | The name of the virtual network. | n/a | yes |
| `address_space` | `list(string)` | The address space that is used by the virtual network. | `["10.10.0.0/16"]` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `vnet_id` | The ID of the virtual network. |
| `vnet_name` | The name of the virtual network. |
| `vnet_address_space` | The address space of the virtual network. |
| `location` | The location of the virtual network. |
