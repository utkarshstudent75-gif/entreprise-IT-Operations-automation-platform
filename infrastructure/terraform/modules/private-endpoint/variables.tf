variable "name" {
  type        = string
  description = "The name of the private endpoint."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the private endpoint."
}

variable "location" {
  type        = string
  description = "The Azure region where the private endpoint will be created."
}

variable "subnet_id" {
  type        = string
  description = "The ID of the subnet where the private endpoint should be created."
}

variable "private_connection_resource_id" {
  type        = string
  description = "The ID of the target resource for the private link service."
}

variable "subresource_names" {
  type        = list(string)
  description = "A list of subresources association (e.g. vault, blob, registry, postgresqlServer, redisCache)."
}

variable "private_dns_zone_ids" {
  type        = list(string)
  description = "A list of Private DNS Zone IDs to link with the Private Endpoint."
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
