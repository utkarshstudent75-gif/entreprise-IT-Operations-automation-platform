# Input variables for the Microsoft Entra ID groups module.


variable "groups" {
  description = "List of Microsoft Entra ID group definitions to provision, typically loaded from organization configuration data."
  type = list(object({
    name             = string
    display_name     = string
    description      = string
    department       = string
    security_enabled = bool
    mail_enabled     = bool
    owners           = list(string)
  }))


  # Validation: Ensure each group name is not empty or whitespace-only
  validation {
    condition     = alltrue([for g in var.groups : length(trimspace(g.name)) > 0])
    error_message = "Group name cannot be empty or only whitespace."
  }

  # Validation: Ensure group names are unique across all groups in the list
  validation {
    condition     = length(var.groups) == length(distinct([for g in var.groups : g.name]))
    error_message = "Each group name must be unique. Duplicate group names are not allowed."
  }

  # Validation: Ensure display name is not empty or whitespace-only
  validation {
    condition     = alltrue([for g in var.groups : length(trimspace(g.display_name)) > 0])
    error_message = "Group display name cannot be empty or only whitespace."
  }

}
