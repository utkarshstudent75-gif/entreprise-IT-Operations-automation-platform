variable "name" {
  type        = string
  description = "The name of the container registry."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the container registry."
}

variable "location" {
  type        = string
  description = "The Azure region where the container registry will be created."
}

variable "sku" {
  type        = string
  description = "The SKU of the container registry (e.g., Premium)."
  default     = "Premium"
}

variable "admin_enabled" {
  type        = bool
  description = "Specifies whether the admin user is enabled."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
