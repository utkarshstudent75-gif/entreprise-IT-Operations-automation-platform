variable "environment" {
  type        = string
  description = "The target deployment environment (dev, test, prod)."

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "The environment variable must be one of: dev, test, prod."
  }
}

variable "project_name" {
  type        = string
  description = "The name of the project, used for naming resources and tagging."

  validation {
    condition     = length(trimspace(var.project_name)) > 0
    error_message = "The project_name variable must not be empty."
  }
}

variable "location" {
  type        = string
  description = "The target Azure region for resources."

  validation {
    condition     = length(trimspace(var.location)) > 0
    error_message = "The location variable must not be empty."
  }
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to Azure resources."
  default     = {}
}
