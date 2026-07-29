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

variable "users" {
  type = list(object({
    id              = string
    first_name      = string
    last_name       = string
    display_name    = string
    email           = string
    department      = string
    job_title       = string
    manager         = string
    account_enabled = bool
    groups          = list(string)
  }))
  description = "List of users with their group memberships from organization.yaml"
}

variable "group_object_ids" {
  type        = map(string)
  description = "Map of group names to their Azure Active Directory object IDs."

  validation {
    condition     = length(var.group_object_ids) > 0
    error_message = "The group_object_ids map must not be empty."
  }
}

variable "user_object_ids" {
  type        = map(string)
  description = "Map of user IDs (slugs) to their Azure Active Directory object IDs."

  validation {
    condition     = length(var.user_object_ids) > 0
    error_message = "The user_object_ids map must not be empty."
  }
}
