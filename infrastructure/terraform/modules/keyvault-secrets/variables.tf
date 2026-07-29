variable "key_vault_id" {
  type        = string
  description = "The Resource ID of the Key Vault."
}

variable "secrets" {
  type        = map(string)
  description = "A map of secret names to secret values."
}
