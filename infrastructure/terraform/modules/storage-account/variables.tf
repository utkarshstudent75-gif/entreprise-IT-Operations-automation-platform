variable "name" {
  type        = string
  description = "The name of the storage account. Must be unique globally."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the storage account."
}

variable "location" {
  type        = string
  description = "The Azure region where the storage account will be created."
}

variable "account_tier" {
  type        = string
  description = "Defines the Tier to use for this storage account."
  default     = "Standard"
}

variable "account_replication_type" {
  type        = string
  description = "Defines the type of replication to use for this storage account."
  default     = "LRS"
}

variable "min_tls_version" {
  type        = string
  description = "The minimum supported TLS version for the storage account."
  default     = "TLS1_2"
}

variable "https_traffic_only_enabled" {
  type        = bool
  description = "Forces HTTPS for all traffic to the storage account."
  default     = true
}

variable "allow_nested_items_to_be_public" {
  type        = bool
  description = "Allow or disallow public access to all blobs or containers in the storage account."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
