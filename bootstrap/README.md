# EITOAP Bootstrap & Deployment Guide

This directory contains the automation tooling to prepare an Azure environment, configure credentials, build infrastructure, and verify the deployment of the **Enterprise IT Operations Automation Platform (EITOAP)**.

---

## 📋 Prerequisites

Before bootstrapping the platform, ensure the following command-line tools are installed on your host system:

| Tool | Purpose | Install Documentation |
|---|---|---|
| **Azure CLI (`az`)** | Azure resource management and authentication | [Install Guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) |
| **Terraform (`terraform`)** | Infrastructure as Code provisioning | [Install Guide](https://developer.hashicorp.com/terraform/downloads) |
| **kubectl (`kubectl`)** | Kubernetes cluster administration | [Install Guide](https://kubernetes.io/docs/tasks/tools/) |
| **Helm (`helm`)** | Kubernetes package manager (deploy charts) | [Install Guide](https://helm.sh/docs/intro/install/) |
| **Docker (`docker`)** | Image builds and local container runner | [Install Guide](https://docs.docker.com/engine/install/) |
| **Git (`git`)** | Version control & source repository management | [Install Guide](https://git-scm.com/downloads) |
| **jq (`jq`)** | JSON processing utility for scripts | `sudo apt install jq` or `brew install jq` |
| **GitHub CLI (`gh`)** * | Optional CLI to automate repository secrets config | [Install Guide](https://cli.github.com/) |

---

## 🚀 Bootstrap Process

The bootstrap process sets up the foundational Azure resources needed for state tracking and CI/CD access:

1. **Configure Environment Settings:**
   Copy the example environment configuration:
   ```bash
   cp bootstrap/.env.example bootstrap/.env
   ```
   Open `bootstrap/.env` and edit defaults as necessary (e.g. `EITOAP_LOCATION` to override the default `eastus` region).

2. **Run the Bootstrap Script:**
   - **Linux/macOS:**
     ```bash
     chmod +x bootstrap/*.sh
     ./bootstrap/bootstrap.sh
     ```
   - **Windows (PowerShell):**
     ```powershell
     .\bootstrap\bootstrap.ps1
     ```

### What the Bootstrap Script Does:
1. **Dependency Checks:** Validates all required CLI tools are installed and provides guidance for any missing ones.
2. **Azure Authentication:** Detects if you are already logged in. If not, prompts for interactive authentication.
3. **Active Subscription:** Lists all available subscriptions, prompts for selection if multiple exist, and updates active Azure context.
4. **Terraform Remote Backend:** Creates a Resource Group (default: `eitoap-tfstate-rg`) and a globally unique Storage Account and Blob Container.
5. **Service Principal Creation/Reuse:** Creates a dedicated AD application with `Contributor` scope for CI/CD pipeline runs. It reuse credentials if they exist.
6. **Federated Identity Credentials (OIDC):** Configures GitHub Actions OIDC federated identity credentials on the service principal, enabling passwordless authentication for the `azure/login@v2` action on specified branches and events (e.g. `workflow_dispatch`).
7. **GitHub Secret Export:** If the GitHub CLI (`gh`) is authenticated, it sets repository action secrets directly. Otherwise, it writes them securely to `bootstrap/github-secrets.txt`.
8. **Terraform Plan & Init:** Runs `terraform init` using dynamic backend inputs and performs `terraform validate` and `terraform plan`.
9. **Terraform Apply Prompt:** Asks if you want to deploy the resources immediately.

---

## 🔐 GitHub Configuration

To trigger automatic GitHub Action builds, configure the repository secrets listed in `bootstrap/github-secrets.txt`:
* `AZURE_CLIENT_ID`
* `AZURE_SUBSCRIPTION_ID`
* `AZURE_TENANT_ID`
* `ACR_NAME`
* `AKS_CLUSTER_NAME`
* `RESOURCE_GROUP`
* `POSTGRES_HOST`
* `REDIS_HOST`
* `KEYVAULT_NAME`

> **Note:** The CI workflows authenticate to Azure via **OIDC federated identity credentials** (not client secrets). The bootstrap script automatically configures these on the Azure AD app registration. The `AZURE_CLIENT_SECRET` is still created and exported for local/tooling use, but the `azure/login@v2` steps in CI only require `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`.

---

## 🏗️ Deployment

Once the infrastructure is created and the secrets are configured:
1. Push your changes to the `master` branch:
   ```bash
   git push origin master
   ```
2. The GitHub Action pipeline (`ci.yml`) will run, build Docker images, push them to ACR, sign them using Cosign, run security vulnerability scans via Trivy, and deploy to AKS via Helm.

---

## 🔍 Verification

To verify that the deployed infrastructure and applications are completely healthy, execute the verification script:
```bash
./bootstrap/verify.sh
```

This script outputs a **PASS/FAIL** report for:
- Azure resources presence (AKS, Key Vault, Database, ACR, Redis)
- Kubernetes pods, deployments, services, namespaces, and load balancer IP allocation
- Database and Redis connection health via backend container readiness checks
- Frontend availability

---

## 🗑️ Cleanup / Tear Down

To tear down the resources interactive:
```bash
./bootstrap/cleanup.sh
```

Choose from:
- **Option 1:** Destroy Terraform-managed development infrastructure.
- **Option 2:** Clean up Terraform state backend (resource group + storage account).
- **Option 3:** Delete Kubernetes Helm workloads and namespaces.
- **Option 4:** Destroy everything.

---

## 🛡️ Disaster Recovery Playbook

If you need to rebuild the environment from scratch (e.g. Trial expiration, Subscription replacement):
1. Create a brand-new Azure subscription.
2. Edit `bootstrap/.env` with your new subscription variables.
3. Run `./bootstrap/bootstrap.sh`. It will create a clean backend and prompt to execute `terraform apply`.
4. Trigger your CI/CD pipeline by pushing to your repository.
5. Run `./bootstrap/verify.sh` to confirm operation.

---

## ⏱️ Expected Execution Times

- **Bootstrap Execution:** ~3-5 minutes
- **Terraform Apply (AKS, DB, Redis, ACR):** ~20-30 minutes
- **GitHub Pipeline (Build & Deploy):** ~8-12 minutes
- **Verification Run:** ~2 minutes
- **Total Provisioning Time:** **~35-50 minutes**
