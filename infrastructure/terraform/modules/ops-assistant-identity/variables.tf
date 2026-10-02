variable "name" {
  type        = string
  description = "Name of the dedicated managed identity for the operations assistant."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group where the dedicated managed identity is created."
}

variable "location" {
  type        = string
  description = "Azure region for the dedicated managed identity."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to the managed identity."
  default     = {}
}

variable "oidc_issuer_url" {
  type        = string
  description = "OIDC issuer URL of the existing AKS cluster."
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace of the assistant backend."
  default     = "backend"
}

variable "service_account_name" {
  type        = string
  description = "Dedicated Kubernetes service account name."
  default     = "ops-assistant"
}

variable "monitoring_resource_group_ids" {
  type        = map(string)
  description = "Only the Azure resource groups where read-only inventory and metrics are allowed."
}
