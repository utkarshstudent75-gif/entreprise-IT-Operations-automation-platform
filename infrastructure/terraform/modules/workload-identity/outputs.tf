output "federated_credential_id" {
  description = "The ID of the provisioned Azure Federated Identity Credential."
  value       = azurerm_federated_identity_credential.this.id
}

output "subject" {
  description = "The subject identifier of the federated credential."
  value       = azurerm_federated_identity_credential.this.subject
}
