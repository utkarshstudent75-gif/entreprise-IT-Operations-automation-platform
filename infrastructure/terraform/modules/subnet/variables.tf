variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which the virtual network and subnets exist."
}

variable "vnet_name" {
  type        = string
  description = "The name of the virtual network in which to create the subnets."
}

variable "subnets" {
  type = map(object({
    name                                          = string
    address_prefixes                              = list(string)
    private_endpoint_network_policies             = optional(string, "Enabled")
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
  description = "A map of subnets to create under the virtual network."
}
