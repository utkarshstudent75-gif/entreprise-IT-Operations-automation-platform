variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the private DNS zones."
}

variable "vnet_id" {
  type        = string
  description = "The ID of the virtual network to link the Private DNS zones to."
}

variable "private_dns_zones" {
  type        = list(string)
  description = "A list of Private DNS zone names to create."
  default = [
    "privatelink.vaultcore.azure.net",
    "privatelink.postgres.database.azure.com",
    "privatelink.redis.cache.windows.net"
  ]
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resources."
  default     = {}
}
