variable "name" {
  type        = string
  description = "The name of the Log Analytics Workspace."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the Log Analytics Workspace."
}

variable "location" {
  type        = string
  description = "The Azure region where the Log Analytics Workspace will be created."
}

variable "retention_in_days" {
  type        = number
  description = "The workspace data retention in days. Possible values are either 7 (for Free Tier only) or range between 30 and 730."
  default     = 30
}

variable "sku" {
  type        = string
  description = "Specifies the SKU of the Log Analytics Workspace."
  default     = "PerGB2018"
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
