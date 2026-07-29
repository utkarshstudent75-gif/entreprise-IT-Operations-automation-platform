variable "principal_id" {
  type        = string
  description = "The principal ID of the Managed Identity."
}

variable "key_vault_id" {
  type        = string
  description = "The ID of the Key Vault."
}

variable "storage_account_id" {
  type        = string
  description = "The ID of the Storage Account."
}

variable "postgresql_server_name" {
  type        = string
  description = "The name of the PostgreSQL Flexible Server."
  default     = null
}

variable "postgresql_resource_group_name" {
  type        = string
  description = "The resource group name of the PostgreSQL Flexible Server."
  default     = null
}

variable "postgresql_admin_tenant_id" {
  type        = string
  description = "The Microsoft Entra ID tenant ID for the Active Directory administrator of PostgreSQL."
  default     = null
}

variable "postgresql_admin_name" {
  type        = string
  description = "The principal name of the Active Directory administrator of PostgreSQL."
  default     = null
}
