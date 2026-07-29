# Subnet Module

This module provisions subnets in an existing Azure Virtual Network (VNet). It supports optional service endpoints, private endpoint network policy settings, and service delegations.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `resource_group_name` | `string` | The name of the resource group in which the virtual network and subnets exist. | n/a | yes |
| `vnet_name` | `string` | The name of the virtual network in which to create the subnets. | n/a | yes |
| `subnets` | `map(object)` | A map of subnets configuration to create. | n/a | yes |

The `subnets` object format:
```hcl
map(object({
  name                                          = string
  address_prefixes                              = list(string)
  private_endpoint_network_policies_enabled     = optional(bool, true)
  private_link_service_network_policies_enabled = optional(bool, true)
  service_endpoints                             = optional(list(string), [])
  delegation = optional(object({
    name = string
    service_delegation = object({
      name    = string
      actions = optional(list(string), [])
    })
  }))
}))
```

## Outputs

| Name | Description |
|------|-------------|
| `subnet_ids` | A map of subnet keys to their Azure resource IDs. |
| `subnet_names` | A map of subnet keys to their names. |
| `subnet_address_prefixes` | A map of subnet keys to their address prefixes. |
