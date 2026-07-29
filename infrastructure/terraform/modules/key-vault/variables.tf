variable "name" {
  type        = string
  description = "The name of the Key Vault."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group in which to create the Key Vault."
}

variable "location" {
  type        = string
  description = "The Azure region where the Key Vault will be created."
}

variable "tenant_id" {
  type        = string
  description = "The Microsoft Entra ID tenant ID that should be used for authorizing requests to this Key Vault."
}

variable "sku_name" {
  type        = string
  description = "The SKU name of the Key Vault (standard or premium)."
  default     = "standard"
}

variable "soft_delete_retention_days" {
  type        = number
  description = "The number of days that items should be retained for once soft-deleted."
  default     = 7
}

variable "purge_protection_enabled" {
  type        = bool
  description = "Is Purge Protection enabled for this Key Vault?"
  default     = true
}

variable "enable_rbac_authorization" {
  type        = bool
  description = "Boolean flag to specify whether Azure Key Vault uses Role Based Access Control (RBAC) for authorization of data actions."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}
