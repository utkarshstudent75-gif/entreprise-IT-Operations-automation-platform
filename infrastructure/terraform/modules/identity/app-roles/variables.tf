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

variable "application_resource_id" {
  type        = string
  description = "The Microsoft Graph resource ID of the application registration where these roles will be created (format: /applications/<objectId>)."

  validation {
    condition     = length(var.application_resource_id) > 0
    error_message = "The application_resource_id variable must not be empty."
  }
}

variable "app_roles" {
  type = map(object({
    display_name         = string
    description          = string
    value                = string
    allowed_member_types = list(string)
  }))
  description = "Map of application roles to create, including display names, descriptions, values, and member types."
  default = {
    "admin" = {
      display_name         = "Platform Administrator"
      description          = "Full administrative access to the IT Operations platform, configuration, and security settings."
      value                = "Platform.Admin"
      allowed_member_types = ["User", "Application"]
    }
    "it_support" = {
      display_name         = "IT Operations Specialist"
      description          = "Access to IT operations dashboards, diagnostics, and management tools."
      value                = "Platform.IT"
      allowed_member_types = ["User"]
    }
    "hr" = {
      display_name         = "HR Operations Specialist"
      description          = "Access to employee records and automation workflows related to onboarding/offboarding."
      value                = "Platform.HR"
      allowed_member_types = ["User"]
    }
    "finance" = {
      display_name         = "Finance Specialist"
      description          = "Access to financial and accounting data and operations on the platform."
      value                = "Platform.Finance"
      allowed_member_types = ["User"]
    }
    "sales" = {
      display_name         = "Sales Specialist"
      description          = "Access to sales performance dashboards and customer integration tools."
      value                = "Platform.Sales"
      allowed_member_types = ["User"]
    }
    "marketing" = {
      display_name         = "Marketing Specialist"
      description          = "Access to marketing automation, analytics, and campaign tools."
      value                = "Platform.Marketing"
      allowed_member_types = ["User"]
    }
    "operations" = {
      display_name         = "Operations Specialist"
      description          = "Access to facilities and operations management dashboards."
      value                = "Platform.Operations"
      allowed_member_types = ["User"]
    }
    "auditor" = {
      display_name         = "Compliance Auditor"
      description          = "ReadOnly access to audit logs, configuration history, and compliance dashboards."
      value                = "Platform.Auditor"
      allowed_member_types = ["User", "Application"]
    }
    "employee" = {
      display_name         = "Standard Employee"
      description          = "General read-only and self-service capabilities on the automation platform."
      value                = "Platform.Employee"
      allowed_member_types = ["User"]
    }
  }
}
