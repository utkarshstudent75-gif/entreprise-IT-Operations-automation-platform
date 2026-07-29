# Azure Kubernetes Service (AKS) Terraform Module

This module provisions an enterprise-ready, cost-optimized Azure Kubernetes Service (AKS) cluster using Azure CNI Overlay networking, OIDC Issuer, and Workload Identity.

## Features

- **Cost-Optimized System Node Pool**: Runs standard `Standard_D2s_v5` nodes, scaled from 1 to 3 nodes with autoscaling enabled. Uses the Free Tier control plane.
- **Azure CNI Overlay**: Efficient pod IP allocation from an overlay network address space, preserving VNet subnet space.
- **OIDC Issuer & Workload Identity**: Ready for secure passwordless authentication for application workloads.
- **Azure AD Integration with Azure RBAC**: Enhances security by delegating Kubernetes authentication and authorization to Entra ID.
- **Disabled Local Accounts**: Mandates the use of Entra ID roles for cluster administration and developer access.
- **API Server Authorized IP Ranges**: Restricts access to the control plane.

## Usage

```hcl
module "aks" {
  source              = "../../modules/aks"
  cluster_name        = "enterprise-dev-aks"
  location            = "eastus"
  resource_group_name = "enterprise-itops-dev-rg"
  vnet_subnet_id      = "/subscriptions/.../subnets/aks-subnet"
  
  api_server_authorized_ip_ranges = ["10.10.1.0/24"]
}
```
