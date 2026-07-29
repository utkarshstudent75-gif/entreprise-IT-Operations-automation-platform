variable "federated_credential_name" {
  type        = string
  description = "The name of the federated identity credential."
}

variable "oidc_issuer_url" {
  type        = string
  description = "The OIDC issuer URL of the AKS cluster."
}

variable "managed_identity_id" {
  type        = string
  description = "The resource ID of the user assigned managed identity."
}

variable "namespace" {
  type        = string
  description = "The Kubernetes namespace where the service account is defined."
  default     = "default"
}

variable "service_account_name" {
  type        = string
  description = "The name of the Kubernetes service account."
}
