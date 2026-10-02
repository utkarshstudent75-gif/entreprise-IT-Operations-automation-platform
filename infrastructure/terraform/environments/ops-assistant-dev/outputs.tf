output "ops_assistant_identity_client_id" {
  description = "Client ID for the read-only AI operations assistant backend identity."
  value       = module.ops_assistant_identity.identity_client_id
}

output "ops_assistant_identity_principal_id" {
  description = "Principal ID for the read-only AI operations assistant identity."
  value       = module.ops_assistant_identity.identity_principal_id
}
