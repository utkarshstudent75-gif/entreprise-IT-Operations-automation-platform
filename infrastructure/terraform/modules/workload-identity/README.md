# Azure Workload Identity Federated Credential Terraform Module

This module provisions an `azurerm_federated_identity_credential` resource. This establishes a trust relationship between a user-assigned managed identity in Azure and a Kubernetes ServiceAccount in AKS. 

This enables Kubernetes workloads (e.g. FastAPI applications) running under the ServiceAccount to authenticate to Azure Active Directory (Microsoft Entra ID) passwordlessly and securely using the AKS OIDC issuer.

## Usage

```hcl
module "workload_identity" {
  source                    = "../../modules/workload-identity"
  federated_credential_name = "fastapi-workload-identity"
  resource_group_name       = "enterprise-itops-dev-rg"
  oidc_issuer_url           = "https://eastus.oic.prod-aks.azure.com/..."
  managed_identity_id       = "/subscriptions/.../userAssignedIdentities/my-identity"
  namespace                 = "dev"
  service_account_name      = "fastapi-sa"
}
```
