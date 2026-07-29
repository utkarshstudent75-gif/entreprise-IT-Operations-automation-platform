variable "project_name" {
  type        = string
  description = "The name of the project, used for resource naming and tagging."
  default     = ""
}

variable "environment" {
  type        = string
  description = "The target deployment environment (dev, test, prod)."
  default     = ""
}

variable "display_name" {
  type        = string
  description = "The base display name of the application registration."
  default     = "Enterprise IT Operations Automation Platform"

  validation {
    condition     = length(trimspace(var.display_name)) > 0
    error_message = "The display_name variable must not be empty."
  }
}
