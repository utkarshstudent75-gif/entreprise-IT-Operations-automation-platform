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

variable "service_principal_object_id" {
  type        = string
  description = "The object ID of the service principal of the application registration."

  validation {
    condition     = length(var.service_principal_object_id) > 0
    error_message = "The service_principal_object_id variable must not be empty."
  }
}

variable "app_role_ids" {
  type        = map(string)
  description = "A map of app role values (e.g. 'Platform.Admin') to their GUID role IDs."

  validation {
    condition     = length(var.app_role_ids) > 0
    error_message = "The app_role_ids map must not be empty."
  }
}

variable "group_object_ids" {
  type        = map(string)
  description = "A map of group names (e.g. 'SG-IT') to their Azure Active Directory object IDs."

  validation {
    condition     = length(var.group_object_ids) > 0
    error_message = "The group_object_ids map must not be empty."
  }
}

variable "role_assignments" {
  type = list(object({
    group_name = string
    role_value = string
  }))
  description = "List of group-to-role assignments."
  default = [
    { group_name = "SG-Executive", role_value = "Platform.Admin" },
    { group_name = "SG-IT", role_value = "Platform.IT" },
    { group_name = "SG-HR", role_value = "Platform.HR" },
    { group_name = "SG-Finance", role_value = "Platform.Finance" },
    { group_name = "SG-Sales", role_value = "Platform.Sales" },
    { group_name = "SG-Marketing", role_value = "Platform.Marketing" },
    { group_name = "SG-Operations", role_value = "Platform.Operations" },
    { group_name = "SG-Audit", role_value = "Platform.Auditor" }
  ]
}
