variable "name" {
  type        = string
  description = "The name of the user assigned managed identity."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the user assigned managed identity."
}

variable "location" {
  type        = string
  description = "The Azure region where the user assigned managed identity will be created."
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
