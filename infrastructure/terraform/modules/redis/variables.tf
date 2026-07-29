variable "name" {
  type        = string
  description = "The name of the Redis Cache."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The Azure region for the Redis Cache."
}

variable "sku_name" {
  type        = string
  description = "The SKU tier of Redis to use (Basic, Standard, Premium)."
  default     = "Basic"
}

variable "family" {
  type        = string
  description = "The SKU family to use (C for Basic/Standard, P for Premium)."
  default     = "C"
}

variable "capacity" {
  type        = number
  description = "The size of the Redis Cache to deploy (0 to 6)."
  default     = 0
}

variable "non_ssl_port_enabled" {
  type        = bool
  description = "Whether the non-SSL port (6379) is enabled."
  default     = false
}

variable "public_network_access_enabled" {
  type        = bool
  description = "Whether public network access is enabled."
  default     = true
}

variable "maxmemory_policy" {
  type        = string
  description = "Redis eviction policy (e.g. allkeys-lru, volatile-lru)."
  default     = "allkeys-lru"
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
