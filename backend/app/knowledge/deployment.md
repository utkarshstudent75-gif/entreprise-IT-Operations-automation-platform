# EITOAP deployment reference

## Application and delivery

- The React/TypeScript frontend and Python/FastAPI backend are the two application workloads in Azure Kubernetes Service (AKS).
- PostgreSQL stores application data; Redis supports caching and rate limiting.
- Terraform declares Azure infrastructure. GitHub Actions tests code and publishes commit-tagged images to Azure Container Registry (ACR).
- Argo CD watches the `master` branch and reconciles Helm releases into AKS. CI updates the image references in Git; CI does not directly deploy to the cluster.
- The standalone operations assistant UI is intended for Azure Static Web Apps. Its browser obtains an Entra access token for the FastAPI API; it must not receive Foundry or Azure management credentials.

## Monitoring

- Prometheus and Grafana run in AKS. Prometheus scrapes application and Kubernetes metrics, and Grafana provides application and Kubernetes dashboards.
- Azure Monitor and Log Analytics are provisioned by the development Terraform environment.
- The assistant's Azure Resource Graph inventory and resource-health tools are read-only and scoped to these resource groups:
  - `enterprise-it-operations-platform-dev-rg`
  - `eitoap-tfstate-rg`
  - `MC_enterprise-it-operations-platform-dev-rg_enterprise-dev-aks_eastus`
- A missing Azure Resource Health record does not mean a resource is healthy.
- Resource inventory exposes resource metadata only. The assistant must never read Terraform state blobs, state contents, secret values, or Key Vault values.

## Operations boundaries

- The assistant is an advisory, read-only diagnostic experience. It does not execute shell commands, run arbitrary KQL, modify Azure resources, restart workloads, or scale deployments.
- Verify current Azure Monitor and AKS live diagnostic integrations before claiming live logs, metrics, pod events, or remediation are available. The initial API only exposes Azure Resource Graph inventory and reported Azure Resource Health.
- Any future restart requires an authenticated operator and an explicit confirmation enforced by the backend. Scaling must be proposed through an approved GitOps change so Argo CD remains authoritative.
