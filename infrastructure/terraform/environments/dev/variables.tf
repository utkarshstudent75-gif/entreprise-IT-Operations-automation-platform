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

variable "vm_size" {
  type        = string
  description = "The VM size to use for nodes in the system node pool."
  default     = "Standard_D2s_v7"
}

variable "postgresql_admin_username" {
  type        = string
  description = "The administrator login name for PostgreSQL."
  default     = "psqladmin"
}

variable "database_name" {
  type        = string
  description = "The database name for the application."
  default     = "eitoap"
}

variable "msgraph_client_id" {
  type        = string
  description = "Microsoft Graph Client ID."
  default     = "placeholder-msgraph-client-id"
}

variable "msgraph_client_secret" {
  type        = string
  description = "Microsoft Graph Client Secret."
  default     = "placeholder-msgraph-client-secret"
  sensitive   = true
}

variable "msgraph_tenant_id" {
  type        = string
  description = "Microsoft Graph Tenant ID."
  default     = "placeholder-msgraph-tenant-id"
}

variable "sms_provider_api_key" {
  type        = string
  description = "SMS Provider API Key."
  default     = "placeholder-sms-api-key"
  sensitive   = true
}

variable "sms_provider_account_sid" {
  type        = string
  description = "SMS Provider Account SID / Sender ID."
  default     = "placeholder-sms-account-sid"
}

variable "enable_private_endpoint" {
  type        = bool
  description = "Controls if Private Endpoints are deployed for PostgreSQL and Redis."
  default     = false
}