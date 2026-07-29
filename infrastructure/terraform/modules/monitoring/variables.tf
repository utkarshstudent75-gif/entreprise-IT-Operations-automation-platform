variable "name" {
  type        = string
  description = "The name of the Application Insights resource."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the Application Insights resource."
}

variable "location" {
  type        = string
  description = "The Azure region where the Application Insights resource will be created."
}

variable "workspace_id" {
  type        = string
  description = "The Resource ID of the Log Analytics Workspace to link this Application Insights resource with."
}

variable "application_type" {
  type        = string
  description = "Specifies the type of Application Insights to create. Valid values are ios, java, phone, store, web, and other."
  default     = "web"
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
