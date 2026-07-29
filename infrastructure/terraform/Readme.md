# Enterprise IT Operations Automation Platform - Infrastructure

This repository contains the Terraform configuration for provisioning the Azure infrastructure for the Enterprise IT Operations Automation Platform.

## Architecture Overview

The platform uses a modular monolith design consisting of:
- **React Frontend**: Deployed on Azure Container Apps.
- **FastAPI Backend**: Modular monolith deployed on Azure Container Apps.
- **PostgreSQL**: Managed relational database via Azure Database for PostgreSQL.
- **Redis**: Caching and session state via Azure Cache for Redis.
- **Microsoft Entra ID & Graph API**: Enterprise directory integration, identity synchronization, and role management.
- **Key Vault**: Secrets management.

---

## Directory Structure

The repository is organized following Terraform best practices:

```text
terraform/
├── Readme.md           # This documentation file
├── versions.tf         # Root Terraform version and required provider block
├── providers.tf        # Root provider configurations
├── variables.tf        # Root variable declarations (with validations)
├── locals.tf           # Project wide local variables and common resource tags
├── outputs.tf          # Root output declarations
│
├── data/               # YAML configuration files for Declarative Identity
│   ├── organization.yaml  # Departments, Groups, and Users schema
│   └── roles.yaml         # Application Roles (Entra ID App Roles) with stable UUIDs
│
├── environments/       # Environment-specific orchestrations (Root Modules)
│   ├── dev/            # Development environment configuration
│   ├── test/           # Testing & QA environment configuration
│   └── prod/           # Production environment configuration
│
└── modules/            # Reusable infrastructure modules
    ├── identity/       # Identity management submodules
    │   ├── users/            # Provisioning of Entra ID users
    │   ├── groups/           # Provisioning of Entra ID security groups
    │   ├── memberships/      # User-to-group mapping
    │   ├── app-registration/ # App registrations for frontend/backend
    │   ├── app-roles/        # Custom App Role definitions
    │   └── role-assignments/ # Azure RBAC and app role assignments
    │
    ├── networking/     # Azure Virtual Networks, subnets, and NSGs
    ├── storage/        # Storage Accounts for assets/logs
    ├── keyvault/       # Secrets, keys, and certificate storage
    ├── postgres/       # PostgreSQL Flexible Server configuration
    ├── redis/          # Redis Cache configuration
    ├── monitoring/     # Log Analytics, Application Insights, Diagnostics
    └── container-apps/ # Azure Container Apps (ACA) env and container definitions
```

---

## Environment Design

Each directory in `environments/` (`dev`, `test`, `prod`) acts as a separate, self-contained **Root Module**. This provides isolation between staging environments and prevents cross-contamination of states.

### Standard File Layout per Environment
Each environment contains:
- `versions.tf`: Lock file for Terraform CLI and provider versions.
- `providers.tf`: Provider setup for `azurerm` and `azuread`.
- `variables.tf`: Declarations of input parameters.
- `terraform.tfvars`: Environment-specific parameter values.
- `backend.tf`: Configures the remote state storage (empty `backend "azurerm" {}` block allowing dynamic input).
- `main.tf`: Coordinates the resource modules (calls the directories in `modules/`).
- `outputs.tf`: Exports environment specific indicators.

---

## Declarative Identity Management (YAML Schemas)

Platform identities are managed declaratively using YAML configurations under the `data/` directory.

### 1. Organization Schema (`data/organization.yaml`)
Stores metadata about the tenant structure, including:
- **Departments**: Defined with unique `code`, human-readable `name`, and financial `cost_center` identifiers.
- **Security Groups**: Mapped to departments and defined with `display_name`, `description`, `security_enabled` indicators, and `owners`.
- **Users**: Structured with names, contact details, `job_title`, `manager` references, and static `groups` memberships.

### 2. Application Roles Schema (`data/roles.yaml`)
Defines Entra ID App Roles assigned to users and applications for fine-grained authorization.
- App roles are defined with stable, static UUID `id` values to prevent re-creation during deployments.
- Includes `allowed_member_types` (e.g., `["User"]`, `["Application"]`) and `enabled` statuses.

---

## How to Run & Validate

### 1. Format Code
To ensure consistency, run:
```bash
terraform fmt -recursive
```

### 2. Local Validation
To test a specific environment without initializing a remote state backend, navigate to its directory and run:
```bash
cd environments/dev
terraform init -backend=false
terraform validate
```

---

## Phase 3 Design Decisions and AKS Architecture

### 1. AKS Control Plane (Free Tier)
* **Decision**: Configured `sku_tier = "Free"`.
* **Rationale**: Avoids the hourly cost of the Standard SLA control plane while meeting dev/test requirements. It provides a 99.5% SLO.

### 2. Networking (Azure CNI Overlay)
* **Decision**: Network plugin set to `azure` with plugin mode set to `overlay`.
* **Rationale**: Traditional Azure CNI assigns VNet IPs to every pod, leading to IP exhaustion. CNI Overlay assigns pods IPs from a dedicated private CIDR block (`10.244.0.0/16`) while nodes are placed in the VNet subnet (`10.10.1.0/24`). This prevents VNet depletion and supports larger microservice workloads.

### 3. Identity and Access (OIDC & Workload Identity)
* **Decision**: Enabled `oidc_issuer_enabled` and `workload_identity_enabled`.
* **Rationale**: Workload Identity allows Kubernetes ServiceAccounts to trust an Azure User-Assigned Managed Identity via federated credentials. Workloads (such as FastAPI) can authenticate passwordlessly to Azure Key Vault, Storage, and Microsoft Graph without managing secrets or rotating keys.

### 4. Entra ID Integration & RBAC
* **Decision**: Disabled local accounts (`local_account_disabled = true`) and enabled Azure RBAC (`azure_rbac_enabled = true`).
* **Rationale**: Enforces Entra ID for all cluster access. No local admin credentials or kubeconfig files can bypass Entra ID logs and authorization.

### 5. VM Size & Node Pool
* **Decision**: Used `Standard_D2s_v7` (adapted from `v5` due to regional availability limits) with cluster autoscaling enabled (min 1, max 3, initial 1).
* **Rationale**: Standard D2s_v7 (2 vCPU, 8 GB RAM) comfortably hosts the microservice workloads. Scaling down to 1 node when idle minimizes credits consumption.

### 6. Preparation for Later Phases
* **ACR Integration**: The `acr-role-assignment` module grants `AcrPull` permission to the AKS Kubelet identity, allowing it to pull microservice images built by CI/CD.
* **Workload Identity**: Configures federated credentials to allow FastAPI workloads running under the `fastapi-sa` ServiceAccount in the `dev` namespace to securely authenticate to Azure resources.

