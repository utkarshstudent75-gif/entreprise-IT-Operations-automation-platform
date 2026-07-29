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
