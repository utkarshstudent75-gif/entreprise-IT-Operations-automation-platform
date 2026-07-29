# Azure Container Registry (ACR) Role Assignment Terraform Module

This module assigns the standard `AcrPull` role to the AKS Kubelet managed identity, granting the AKS cluster permission to pull Docker containers from the registry without enabling local admin user accounts or registry passwords.

## Usage

```hcl
module "acr_role_assignment" {
  source       = "../../modules/acr-role-assignment"
  acr_id       = "/subscriptions/.../containerRegistries/myregistry"
  principal_id = "object-id-of-aks-kubelet-identity"
}
```
