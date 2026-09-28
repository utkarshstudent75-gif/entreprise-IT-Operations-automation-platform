# Enterprise IT Operations Automation Platform

<p align="center">
  <img src="https://github.com/user-attachments/assets/fd3a98fa-a0e3-4bc5-a468-998e77dc39dc" alt="Gemini-generated EITOAP workflow" width="100%">
</p>

**EITOAP** is a self-service IT operations platform for automating common help-desk tasks. It brings together a browser-based application, an API, and cloud infrastructure to support workflows such as password resets with one-time passcodes (OTPs), tickets, software requests, notifications, and audit records.

The application is built with **React and TypeScript** on the frontend and **FastAPI** on the backend. PostgreSQL stores application data, while Redis supports caching and rate limiting. The project also demonstrates how to package, test, provision, deploy, and monitor an application using Docker, Terraform, Azure, Kubernetes, GitHub Actions, and Argo CD.

> **Deployment model:** The AKS deployment runs two application workloads: one frontend and one modular backend. Authentication, password resets, tickets, workflows, notifications, and auditing are backend features, not separate AKS microservices. The repository's Docker Compose file represents an older, separate multi-container local topology.

## Technology stack

| Area | Technologies | Purpose |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite, Material UI | Browser interface and local development server |
| Backend | Python 3.12, FastAPI, Pydantic, Uvicorn | REST API and application features |
| Data | PostgreSQL, SQLAlchemy, Alembic | Relational storage, ORM, and schema migrations |
| Cache | Redis | Caching and request rate limiting |
| Local containers | Docker, Docker Compose | Run PostgreSQL and Redis locally; an older full-stack Compose setup is also included |
| Cloud infrastructure | Microsoft Azure, Terraform | Provision Azure resources and manage infrastructure as code |
| Application runtime | Kubernetes, AKS, Helm | Run and configure the frontend and backend workloads |
| Delivery | GitHub Actions, Azure Container Registry (ACR), Argo CD | Test and build images, publish them, and reconcile Git-declared deployments |
| Observability | Prometheus, Grafana, Azure Monitor / Log Analytics | Application and cluster metrics, dashboards, alerts, and Azure diagnostics |

## How the implementation works

### Application request flow

1. A user interacts with the React frontend.
2. The frontend sends API requests to the FastAPI backend.
3. The backend handles application modules and reads or writes PostgreSQL data; Redis is available for caching and rate limiting.
4. Notification delivery is behind a provider setting. Local development should use the `console` provider; real SMS delivery needs provider credentials.

### Build and Azure delivery flow

1. GitHub Actions runs backend and frontend checks, tests, security scans, and Helm/Terraform validation.
2. On a push to `master`, the workflow builds frontend and backend container images and publishes them to ACR using the commit SHA as the image tag.
3. The workflow updates `deploy/helm/values/dev.yaml` with that tag and pushes the change to Git.
4. Argo CD watches the Git repository and reconciles the Helm releases in AKS. CI publishes images and updates Git; it does not deploy directly to the cluster.
5. Prometheus scrapes application and Kubernetes metrics, and Grafana presents dashboards and alert rules.

### Architecture diagram

The diagram below shows the Azure/AKS deployment. Terraform provisions the Azure environment; local development uses Docker containers for its data services.

![EITOAP application, Azure, CI/CD, GitOps, and observability architecture](./docs/architecture/eitoap-architecture.svg)

## Build and run locally

The steps below run the API and frontend directly on your computer, with PostgreSQL and Redis in Docker. This is the recommended way to understand and develop the application.

### 1. Install prerequisites

- Git
- Python 3.12
- Node.js and npm
- Docker Desktop with the Docker Compose plugin

### 2. Clone the repository

```powershell
git clone https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform.git
Set-Location entreprise-IT-Operations-automation-platform
```

For a personal copy, fork the repository on GitHub and clone your fork's URL instead.

### 3. Configure local settings

Create a local environment file from the example:

```powershell
Copy-Item backend/.env.example backend/.env
```

On macOS or Linux, use `cp backend/.env.example backend/.env` instead. Open `backend/.env` and set `NOTIFICATION_PROVIDER=console`. For this local setup, keep the database and Redis hosts set to `localhost` and use the local Compose database credentials (`postgres` / `postgres`). Clear the example's `<your-...>` placeholder values for Entra ID and SMS credentials unless you have configured those integrations. The example file is for local development only; never commit secrets or use these local credentials in Azure.

### 4. Start PostgreSQL and Redis

From the repository root:

```powershell
docker compose up -d postgres redis
docker compose ps
```

Wait until both services are running before starting the API. Compose publishes PostgreSQL on port `5432` and Redis on port `6379`.

### 5. Install and start the API

Open a terminal in the repository, then run:

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Keep this terminal open. The API is available at <http://localhost:8000>; interactive API documentation is at <http://localhost:8000/docs>.

On macOS or Linux, use the equivalent commands:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Install and start the frontend

In a second terminal, from the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev -- --host 0.0.0.0
```

Open <http://localhost:5173>. Vite proxies API requests to `http://localhost:8000` by default.

### 7. Confirm the application is running

- Open <http://localhost:5173> and verify the frontend loads.
- Open <http://localhost:8000/docs> to inspect the API.
- Open <http://localhost:8000/api/v1/health> to check the API health endpoint.
- Run `docker compose ps` from the repository root to check the local data containers.

### Optional: run the project checks

With the local PostgreSQL and Redis services running, install the backend test dependencies and run the backend tests:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-test.txt
.\.venv\Scripts\python.exe -m pytest
```

In another terminal, run the frontend checks:

```powershell
Set-Location frontend
npm run lint
npm run build
```

### Stop local services

Stop the containers from the repository root:

```powershell
docker compose down
```

This preserves the named data volumes. To also delete the local PostgreSQL, Redis, and pgAdmin data, run `docker compose down --volumes`; this deletion is irreversible.

> **Legacy Compose option:** `docker compose up --build` starts the repository's older multi-container topology, including separate backend service entry points and pgAdmin. It is distinct from both the recommended local API setup above and the two-workload AKS deployment. Treat it as a development-only configuration; do not expose it as a production environment.

## Deploy to Azure

The Azure path provisions a development environment with Terraform, builds and publishes images through GitHub Actions, and uses Argo CD to deploy the Git-declared configuration. Provisioning and running Azure services can incur charges. Use a dedicated non-production subscription, review the Terraform plan, and tear down resources when finished.

### 1. Install tools and prepare accounts

Install and sign in to:

- Azure CLI (`az`), Terraform, `kubectl`, Helm, Docker, Git, and `jq`
- GitHub CLI (`gh`) for automated GitHub secret setup; it is optional if you configure repository settings manually

You also need an Azure subscription with permission to create the configured resources and Entra identities, plus a GitHub repository where Actions can run and update deployment configuration.

The Bash bootstrap script is the recommended route and is intended for Bash on Linux, macOS, or WSL. A Windows PowerShell bootstrap script is also available, but it does not configure GitHub through `gh`; set up the GitHub Actions secrets and variables yourself when using it.

### 2. Fork and configure the repository

For a fork, update the Git repository URLs and branch names in the Argo CD manifests under `deploy/argocd/`. The manifests and CI workflow currently target `master`; either use that branch for your fork or update all related workflow, GitOps, and Argo CD branch settings consistently.

The CI workflow reads `ACR_NAME` and `ACR_LOGIN_SERVER` as **GitHub Actions repository variables**. Confirm they contain the ACR name and login server created for your Azure environment. The bootstrap helper can configure Azure credentials, but values written as GitHub secrets do not satisfy workflow references to repository variables.

### 3. Review Azure costs and security before provisioning

The development Terraform configuration includes a Windows validation workstation VM with a public IP. Its current RDP rule allows inbound access from `*`. Before applying, change `allowed_inbound_rdp_ips` in `infrastructure/terraform/environments/dev/main.tf` to your trusted public IP CIDR (for example, `<your-ip>/32`). Do not provision the default open RDP rule.

AKS nodes, the validation VM, Azure Database for PostgreSQL, Redis, load balancers, monitoring storage, and other resources may incur charges. Check your subscription quota, region availability, and expected cost before applying. Trial credits do not guarantee that the deployment is free.

### 4. Configure and run the Azure bootstrap

From the repository root, copy the example configuration:

```bash
cp bootstrap/.env.example bootstrap/.env
```

Edit `bootstrap/.env` and set the Azure region, project and environment names, GitHub repository (`organization/repository`), and OIDC branch settings for your fork. Do not put this file or generated credentials in source control.

Authenticate with Azure (`az login`) and, if using automatic GitHub configuration, GitHub CLI (`gh auth login`). Then run:

```bash
bash bootstrap/bootstrap.sh
```

Review the selected subscription and every Terraform plan prompt before approving an apply. The bootstrap process prepares remote Terraform state, creates or configures the GitHub OIDC identity, initializes and validates Terraform, and displays a plan. Applying provisions the configured Azure development resources, including AKS, ACR, PostgreSQL, Redis, Key Vault, diagnostics, and the validation workstation. Provisioning can take 20–30 minutes or longer.

When the apply succeeds, bootstrap retrieves AKS credentials and writes deployment metadata to `bootstrap/.bootstrap-output.json`. This file contains sensitive values and is needed by the cleanup helper: protect it, do not commit or share it, and keep it until teardown. If `gh` is unavailable or not authenticated, follow the script's instructions to configure the required GitHub Actions secrets manually.

### 5. Configure GitHub Actions and publish the first images

In your GitHub repository, open **Settings → Secrets and variables → Actions**:

- Add the Azure OIDC secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` if bootstrap did not add them.
- Set the repository variables `ACR_NAME` and `ACR_LOGIN_SERVER` to the provisioned registry's name and login server. Do not set them only as secrets.
- Confirm GitHub Actions has permission to write repository contents; the GitOps job commits updated image tags to the branch.

Push a change to `master` (or manually run the workflow for checks). Image publishing and the GitOps tag update run on a push to `master`; pull requests and feature branches run validation but do not publish images. Confirm the workflow completes and that both image tags have been updated in `deploy/helm/values/dev.yaml`.

### 6. Install the ingress controller

Terraform does not install the NGINX Ingress Controller required by the frontend chart. Install it after connecting `kubectl` to the provisioned AKS cluster:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace --wait
kubectl get svc -n ingress-nginx
```

The controller uses an Azure LoadBalancer by default, which can incur additional charges. The frontend Ingress does not currently configure TLS; do not use it for sensitive public traffic without setting up TLS and an appropriate DNS name.

### 7. Install Argo CD and sync the application

After the first frontend and backend images are available in ACR, install Argo CD in the cluster and apply the root Application:

```bash
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl rollout status deployment/argocd-server -n argocd --timeout=5m
kubectl apply -f deploy/argocd/root-app.yaml -n argocd
kubectl get applications -n argocd
kubectl get pods -A
```

The root Application discovers the frontend, backend, and common Helm Applications. Wait for the Applications to become `Synced` and `Healthy`. For a repeatable or production deployment, use a version-pinned Argo CD installation manifest rather than the moving `stable` URL.

Once the frontend Application is healthy, inspect the ingress and load balancer:

```bash
kubectl get ingress -n frontend
kubectl get svc -n ingress-nginx
```

Use the host and address shown by Kubernetes to reach the frontend. If you forked the repository, verify that the Argo CD source URLs, branch, and image repositories point to your fork and ACR.

### 8. Install monitoring

The observability Helm chart is installed separately. Create its expected Grafana secret without putting the password in source control:

```bash
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
read -rsp "Grafana admin password: " GRAFANA_ADMIN_PASSWORD
echo
kubectl create secret generic grafana-admin -n monitoring \
  --from-literal=admin-password="$GRAFANA_ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
unset GRAFANA_ADMIN_PASSWORD

helm upgrade --install observability deploy/helm/observability \
  --namespace monitoring --create-namespace --wait --timeout 10m
kubectl get pods,pvc -n monitoring
```

If a monitoring pod remains `Pending`, inspect it with `kubectl describe pod -n monitoring <pod-name>` and check node capacity and persistent-volume events. The chart's CPU and memory requests may need adjustment to fit the cluster.

To open Grafana and Prometheus locally, run these commands in separate terminals:

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Open <http://localhost:3000> and <http://localhost:9090>. Use the Grafana password you created above. The backend metrics endpoint is available at `/metrics`; Prometheus evaluates the provisioned application and Kubernetes alert rules. External alert notifications require an Alertmanager receiver to be configured.

### 9. Verify and clean up

The bootstrap verification helper checks Azure resources, Kubernetes connectivity, workload rollouts, and application readiness:

```bash
bash bootstrap/verify.sh
```

Check Argo CD and monitoring separately:

```bash
kubectl get applications -n argocd
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

When finished, run the Azure cleanup script from the repository root:

```bash
bash bootstrap/cleanup.sh
```

Choose the full-environment teardown option only when you intend to delete the AKS environment and its Terraform state storage. This permanently removes Azure resources and remote state. The helper does not remove the bootstrap-created Entra service principal/federated credentials or GitHub Actions secrets and variables; review and remove project-only identities and settings separately. Finally, check Azure Cost Management for remaining resources. Stopping AKS alone does not stop charges for databases, caches, storage, and other services.

## Repository layout

```text
backend/                 FastAPI application, feature modules, migrations, and tests
frontend/                React + TypeScript application
deploy/argocd/           Argo CD root and child Applications
deploy/helm/             Frontend, backend, common, and observability charts
deploy/kubernetes/       Kubernetes manifests and overlays
infrastructure/terraform Azure infrastructure modules and environments
bootstrap/               Azure bootstrap, GitHub setup, verification, and cleanup
scripts/                 Validation workstation and GitOps helper scripts
docs/architecture/       Application and infrastructure architecture diagram
docker-compose.yml       Local data services and legacy full-stack topology
```

## Further documentation

- [Observability guide](./docs/phase-4-observability.md) — monitoring design, metrics, dashboards, alerts, and troubleshooting.
- [Architecture diagram](./docs/architecture/eitoap-architecture.svg) — application and Azure deployment flow.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE).
