# Network Security Group Module

This module provisions an Azure Network Security Group (NSG) with customizable security rules and associates it with a subnet.

## Inputs

| Name | Type | Description | Default | Required |
|------|------|-------------|---------|:--------:|
| `name` | `string` | The name of the network security group. | n/a | yes |
| `resource_group_name` | `string` | The name of the resource group in which to create the network security group. | n/a | yes |
| `location` | `string` | The Azure region where the network security group will be created. | n/a | yes |
| `subnet_id` | `string` | The ID of the subnet to associate with this Network Security Group. | n/a | yes |
| `security_rules` | `list(object)` | Custom security rules to apply to the Network Security Group. | `[]` | no |
| `tags` | `map(string)` | A mapping of tags to assign to the resource. | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| `nsg_id` | The ID of the Network Security Group. |
| `nsg_name` | The name of the Network Security Group. |
| `location` | The location of the Network Security Group. |
