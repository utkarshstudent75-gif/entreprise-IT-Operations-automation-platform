variable "name" {
  type        = string
  description = "The name of the PostgreSQL Flexible Server."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group."
}

variable "location" {
  type        = string
  description = "The Azure region for the server."
}

variable "postgresql_version" {
  type        = string
  description = "The version of PostgreSQL to deploy."
  default     = "16"
}

variable "administrator_username" {
  type        = string
  description = "The administrator login name."
  default     = "psqladmin"
}

variable "administrator_password" {
  type        = string
  description = "The administrator login password."
  sensitive   = true
}

variable "sku_name" {
  type        = string
  description = "The SKU name for the server (compute + size)."
  default     = "B_Standard_B1ms"
}

variable "storage_mb" {
  type        = number
  description = "Max storage size allowed for the server in MB."
  default     = 32768
}

variable "backup_retention_days" {
  type        = number
  description = "The backup retention days for the server."
  default     = 7
}

variable "public_network_access_enabled" {
  type        = bool
  description = "Whether public network access is enabled."
  default     = true
}

variable "firewall_rules" {
  type = map(object({
    start_ip_address = string
    end_ip_address   = string
  }))
  description = "A map of firewall rules to apply to the server."
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}

variable "tenant_id" {
  type        = string
  description = "The Microsoft Entra ID Tenant ID for the server authentication configuration."
  default     = null
}
