variable "subscription_id" {
  type        = string
  description = "Subscription containing the existing EITOAP resources."
}

variable "tenant_id" {
  type        = string
  description = "Entra tenant containing the AKS cluster and workload identity."
}

variable "application_resource_group_name" {
  type        = string
  description = "Existing application resource group."
}

variable "terraform_state_resource_group_name" {
  type        = string
  description = "Existing resource group containing the Terraform state storage account."
}

variable "aks_node_resource_group_name" {
  type        = string
  description = "Existing AKS-managed node resource group."
}

variable "oidc_issuer_url" {
  type        = string
  description = "OIDC issuer URL of the existing AKS cluster."
}

variable "location" {
  type        = string
  description = "Azure region for the managed identity."
}
