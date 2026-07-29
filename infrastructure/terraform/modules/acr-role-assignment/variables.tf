variable "acr_id" {
  type        = string
  description = "The resource ID of the Azure Container Registry."
}

variable "principal_id" {
  type        = string
  description = "The principal ID of the AKS Kubelet identity that needs AcrPull permission."
}
