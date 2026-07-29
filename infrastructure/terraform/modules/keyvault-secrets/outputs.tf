output "secret_ids" {
  description = "A map of secret names to their Key Vault secret IDs."
  value       = { for k, v in azurerm_key_vault_secret.secret : k => v.id }
}
