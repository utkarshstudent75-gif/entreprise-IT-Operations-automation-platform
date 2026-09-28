# Enterprise IT Operations Automation Platform (EITOAP)

EITOAP is a self-service IT operations application that automates routine helpdesk work, especially password resets with one-time-passcode (OTP) verification. It combines a React frontend with a FastAPI backend and PostgreSQL/Redis data services.

The AKS deployment is a **two-workload application**: one frontend and one modular backend. Backend features such as authentication, password reset, tickets, workflows, notifications, and audit records are modules, not separate AKS microservices. The repository also retains a separate, older multi-container Docker Compose topology for local development.

## Architecture

![EITOAP architecture: user traffic, Azure infrastructure, CI/CD, GitOps, and monitoring](./docs/architecture/eitoap-architecture.svg)

The diagram shows how browser traffic reaches the application, how GitHub Actions builds and publishes images for Argo CD to deploy, how Terraform provisions Azure infrastructure, and how Prometheus/Grafana provide monitoring. In the Azure development configuration, PostgreSQL and Redis are managed Azure services; local development uses containers.

## Run locally

### Prerequisites

- Git
- Python 3.12 and `pip`
- Node.js and npm
- Docker with the Docker Compose plugin

### Start the data services

From the repository root, create a local backend environment file:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` for local development. Set `DATABASE_URL` to use the Compose service hostname `postgres:5432/eitoap` with the local Compose credentials, `REDIS_HOST=redis`, `REDIS_URL=redis://redis:6379/0`, and `NOTIFICATION_PROVIDER=console` unless you have configured a real SMS provider. The backend maps these Compose hostnames to loopback when run directly on the host; in containers, Docker DNS resolves them to the Compose services. Never put production credentials in this file.

Start just PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

### Start the API and frontend

In a terminal:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev -- --host 0.0.0.0
```

Open the frontend at <http://localhost:5173> and the API docs at <http://localhost:8000/docs>. The Vite development server proxies API requests to `localhost:8000`.

To stop the local database/cache containers:

```bash
docker compose down
```

This keeps the named data volumes. To also remove the local PostgreSQL, Redis, and pgAdmin data, use `docker compose down --volumes`; that deletion is irreversible.

### Optional: run the full Docker Compose topology

`docker compose up --build` starts the frontend, an API gateway, separate backend service entry points, PostgreSQL, Redis, and pgAdmin. This is a legacy/local topology and differs from the two-workload AKS deployment. It uses development-only configuration; do not expose it as a production environment.

## Deploy to Azure

### Before provisioning

Use a dedicated non-production Azure subscription. Check regional VM quota, Azure trial-credit limits, and expected costs before applying Terraform. AKS worker nodes, PostgreSQL, Redis, the validation VM, and monitoring can incur charges while running; trial credits do not guarantee that resources are free.

The current `dev` Terraform configuration **includes a Windows validation workstation VM by default**, with a public IP and RDP allowed from `*`. Before applying, review `infrastructure/terraform/environments/dev/main.tf` and restrict `allowed_inbound_rdp_ips` to your trusted public IP CIDR (for example, `<your-ip>/32`). If you do not need the workstation, disable/remove that module before applying; there is currently no documented opt-out variable. Review the complete Terraform plan before approving it.

### Requirements

Install and authenticate the following tools:

- Azure CLI (`az`), Terraform, `kubectl`, Helm, Docker, Git, and `jq`
- GitHub CLI (`gh`) is optional; without it, bootstrap writes values for manual GitHub configuration
- An Azure identity permitted to create the required Azure resources and Entra application/federated credentials
- A GitHub repository where Actions can run and the workflow can update the GitOps image tags

### Provision Azure infrastructure and GitHub OIDC

From the repository root, configure the bootstrap defaults:

```bash
cp bootstrap/.env.example bootstrap/.env
```

Set the region, project/environment names, GitHub repository, and branches to match your environment. Then run:

```bash
bash bootstrap/bootstrap.sh
```

The script selects the Azure subscription, creates a Terraform state resource group/storage account, configures a subscription-scoped Contributor service principal and GitHub OIDC credentials, then initializes and validates Terraform, shows a plan, and asks before applying. Applying provisions the Azure development environment, including AKS, ACR, PostgreSQL, Redis, Key Vault, diagnostics, and the validation workstation. After a successful apply it fetches AKS credentials and writes deployment outputs to the git-ignored `bootstrap/.bootstrap-output.json`.

Keep that metadata file protected until teardown: the cleanup script uses it to find the resource groups and state storage. It contains credentials, so never commit or share it. The bootstrap process can configure GitHub Actions secrets with an authenticated `gh`; otherwise, follow its instructions for manual configuration. Remove any local plaintext secrets file after you have securely configured GitHub.

For Windows, `bootstrap/bootstrap.ps1` is available. It performs Terraform setup but writes credentials to a local file rather than configuring GitHub through `gh`; configure the repository’s Actions secrets and variables yourself. Bash/WSL is the recommended path for the complete automated GitHub-secret setup.

### Configure a fork and start GitOps delivery

If deploying a fork, update the repository URL and branch in the Argo CD application manifests under `deploy/argocd/`, update both image repository names in `deploy/helm/values/dev.yaml` to your ACR, and configure the CI workflow/repository settings for that registry. The current workflow publishes images on `master` and pushes the new commit-SHA tags to `deploy/helm/values/dev.yaml`; it needs permission to write contents to the branch it updates.

The CI workflow uses these GitHub Actions secrets for Azure OIDC:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

It also reads `ACR_NAME` and `ACR_LOGIN_SERVER` as **repository variables**. Set them to the ACR values created by Terraform; the bootstrap helper may export values as secrets, which does not populate Actions variables.

The Terraform configuration does not install the NGINX Ingress Controller required by the frontend chart. Install it before syncing the application:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace --wait
kubectl get svc -n ingress-nginx
```

The controller Service uses an Azure LoadBalancer by default, which can incur charges. The frontend Ingress currently has no TLS configuration; do not use it for production or sensitive public traffic without configuring TLS and a suitable DNS name.

Once the cluster is provisioned and the workflow’s first image build/push has succeeded, install Argo CD in AKS using the official [installation guide](https://argo-cd.readthedocs.io/en/stable/getting_started/). For a learning environment, the basic install is:

```bash
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl rollout status deployment/argocd-server -n argocd --timeout=5m
kubectl apply -f deploy/argocd/root-app.yaml -n argocd
kubectl get applications -n argocd
kubectl get pods -A
```

The root Application discovers the frontend, backend, and common Helm Applications. Check that they become `Synced` and `Healthy`. CI updates Git; Argo CD reconciles that desired state into AKS—CI does not deploy directly to the cluster. For repeatable or production installs, use a version-pinned Argo CD release manifest instead of the moving `stable` URL.

### Install monitoring

The observability chart is installed separately from the Argo CD root Application. Create the Grafana password Secret without putting the password in shell history:

```bash
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
read -rsp "Grafana admin password: " GRAFANA_ADMIN_PASSWORD
echo
kubectl create secret generic grafana-admin -n monitoring \
  --from-literal=admin-password="$GRAFANA_ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
unset GRAFANA_ADMIN_PASSWORD
```

Install Prometheus and Grafana:

```bash
helm upgrade --install observability ./deploy/helm/observability \
  --namespace monitoring --create-namespace --wait --timeout 10m
kubectl get pods,pvc -n monitoring
```

After the application syncs, retrieve the ingress address:

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
kubectl get ingress -n frontend
```

The controller’s external IP serves the frontend at `http://<EXTERNAL-IP>/` and routes `/api` to the backend.

If monitoring pods remain `Pending`, inspect their Events with `kubectl describe pod -n monitoring <pod-name>`; insufficient node CPU/memory or an unbound volume can prevent scheduling. The default chart requests CPU and memory in `deploy/helm/observability/values.yaml`; tune those values only after checking node capacity.

Port-forward from separate terminals:

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Open Grafana at <http://localhost:3000> and Prometheus at <http://localhost:9090>. Use the Grafana password created above.

### Verify the environment

The bootstrap verification helper checks Azure resources, Kubernetes connectivity, workload rollouts, and application readiness:

```bash
bash bootstrap/verify.sh
```

It does not verify Argo CD synchronization or the monitoring stack. Check those separately:

```bash
kubectl get applications -n argocd
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

## Validation workstation scripts

The PowerShell scripts in `scripts/` manage the optional Windows validation workstation, not the application deployment:

- `Install-Applications.ps1`, `Configure-VM.ps1`, and `Configure-Startup.ps1` configure software, Windows settings, and browser startup when run elevated on the VM.
- `Invoke-HealthCheck.ps1` checks the workstation, Azure/AKS, and application readiness. Pass your real resource group, cluster, and dashboard URL rather than relying on its example defaults.
- `Destroy-ValidationEnvironment.ps1` targets the validation VM and related identity/password resources while preserving the main AKS/database infrastructure.
- **Caution:** `Provision-ValidationVM.ps1` runs `terraform apply -auto-approve` for the entire `dev` Terraform environment; despite its name, it is not a VM-only provision command. Review the Terraform configuration and plan first.
- `update-gitops-image-tags.py` is a CI helper that updates both frontend and backend image tags to a commit SHA; it is normally run by GitHub Actions.

## Cleanup and cost control

Stop local containers when finished with `docker compose down`. Add `--volumes` only when you intentionally want to delete local database/cache data.

To remove only the validation workstation while keeping the shared Azure environment, run from PowerShell:

```powershell
.\scripts\Destroy-ValidationEnvironment.ps1
```

For the final Azure teardown, run from the repository root:

```bash
bash bootstrap/cleanup.sh
```

Choose **option 4** only when you intend to destroy the complete personal environment. It removes the application Helm releases/namespaces, destroys the development Terraform resources/resource group, and then deletes the Terraform state resource group and storage account. If Terraform destroy fails, the script can offer to delete the development resource group directly. This permanently removes the remote Terraform state; keep that backend if you plan to reuse the environment, or back up state securely before deleting it. The script is destructive and asks for confirmation.

The cleanup helper does not remove the bootstrap-created Entra service principal/federated credentials or GitHub Actions secrets/variables. After verifying that the identity is dedicated to this project and not shared, remove those credentials/permissions from Entra and GitHub manually. Finally, inspect the Azure subscription’s resource groups and Cost Management for leftovers. Stopping AKS alone does not stop charges for managed databases, caches, storage, or other resources.

## DevOps concepts covered

- Local development with Docker, Docker Compose, PostgreSQL, Redis, and migrations
- CI testing, linting, security/container scans, SBOMs, and Helm/Terraform validation
- Azure infrastructure as code with Terraform and remote state
- Docker image publishing to Azure Container Registry
- Kubernetes and Helm deployment with probes, autoscaling, disruption budgets, and network policies
- GitOps delivery with Argo CD and Git as the desired state
- OIDC/workload identity and Key Vault-based secrets
- Prometheus/Grafana metrics, dashboards, and alert rules

## Repository map

```text
backend/                 FastAPI application, services, and tests
frontend/                React + TypeScript application
deploy/argocd/           Argo CD root and child Applications
deploy/helm/             Frontend, backend, shared, and observability charts
deploy/kubernetes/       Kubernetes manifests and environment overlays
infrastructure/terraform Azure infrastructure and validation workstation
bootstrap/               Azure bootstrap, verification, GitHub secrets, cleanup
scripts/                 Validation workstation and GitOps helper scripts
docs/architecture/       Architecture diagram
```

## License

This project is licensed under the MIT License.
