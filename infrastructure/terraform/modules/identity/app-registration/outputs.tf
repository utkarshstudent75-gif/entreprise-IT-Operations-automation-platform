output "application_resource_id" {
  description = "The Microsoft Graph resource ID of the App Registration (format: /applications/<objectId>)."
  value       = azuread_application.app.id
}

output "client_id" {
  description = "The client ID of the App Registration."
  value       = azuread_application.app.client_id
}

output "object_id" {
  description = "The object ID of the App Registration."
  value       = azuread_application.app.object_id
}

output "service_principal_object_id" {
  description = "The object ID of the associated service principal."
  value       = azuread_service_principal.sp.object_id
}
