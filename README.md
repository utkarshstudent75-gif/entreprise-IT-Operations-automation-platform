# Enterprise IT Operations Automation Platform

<p align="center">
  <img src="https://github.com/user-attachments/assets/fd3a98fa-a0e3-4bc5-a468-998e77dc39dc" alt="Gemini-generated EITOAP workflow" width="100%">
</p>

EITOAP is a self-service IT operations platform for common help-desk tasks, including password resets with one-time passcodes (OTPs), tickets, software requests, notifications, and audit records.

The browser application uses React and TypeScript. A FastAPI backend provides the API, PostgreSQL stores application data, and Redis supports caching and rate limiting. The project also demonstrate[...]

> **Deployment model:** AKS runs two application workloads: one frontend and one modular backend. Features such as authentication, password resets, tickets, and workflows are backend modules, not [...]

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, Material UI |
| Backend | Python 3.12, FastAPI, Pydantic, Uvicorn |
| Data | PostgreSQL, SQLAlchemy, Alembic, Redis |
| Containers | Docker, Docker Compose |
| Cloud and infrastructure | Microsoft Azure, Terraform, Azure Kubernetes Service (AKS), Kubernetes, Helm |
| Delivery | GitHub Actions, Azure Container Registry (ACR), Argo CD |
| Monitoring | Prometheus, Grafana, Azure Monitor / Log Analytics |

## How it works

1. A user sends requests through the React frontend to the FastAPI backend.
2. The backend uses PostgreSQL for application data and Redis for caching and rate limiting.
3. GitHub Actions tests the code and builds the frontend and backend images.
4. On pushes to `master`, CI publishes commit-tagged images to ACR and updates the image tags in Git.
5. Argo CD reconciles the Git-declared Helm releases into AKS. CI updates Git; it does not deploy directly to the cluster.
6. Prometheus collects application and Kubernetes metrics, which Grafana displays in dashboards.

![EITOAP Azure, application, CI/CD, GitOps, and monitoring architecture](./docs/architecture/eitoap-architecture.svg)

## Screenshots

The repository includes selected screenshots from the project walkthrough. The original screenshot document also contains OTPs and account details; redact those values before sharing or publishing[...]

<details>
<summary>View application, deployment, monitoring, and CI screenshots</summary>

### Application

![EITOAP frontend](./docs/screenshots/app-home.png)

### Argo CD

![Argo CD applications](./docs/screenshots/argocd-applications.png)

![Argo CD application sync status](./docs/screenshots/argocd-sync-status.png)

### Monitoring

![Grafana dashboards](./docs/screenshots/grafana-dashboards.png)

![Grafana application metrics](./docs/screenshots/grafana-application-metrics.png)

![Grafana Kubernetes metrics](./docs/screenshots/grafana-kubernetes-metrics.png)

### GitHub Actions

![GitHub Actions checks](./docs/screenshots/github-actions-checks.png)

![GitHub Actions pipeline](./docs/screenshots/github-actions-pipeline.png)

</details>

## Run locally with Docker Compose

### Prerequisites

- Git
- Docker Desktop with Docker Compose (v3.9 or later)
- At least 4GB of available RAM allocated to Docker

### 1. Clone the repository

```powershell
git clone https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform.git
Set-Location entreprise-IT-Operations-automation-platform
```

For your own deployment, fork the repository and clone your fork.

### 2. Configure local settings

```powershell
Copy-Item backend/.env.example backend/.env
```

In `backend/.env`, set `NOTIFICATION_PROVIDER=console`, ensure database and cache services are configured to connect to their containerized instances (e.g., `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/eitoap`, `REDIS_URL=redis://redis:6379`), and clear the example Entra ID/SMS placeholders unless you configured those integrations.

### 3. Start all services with Docker Compose

From the repository root, bring up all services (database, cache, backend services, and frontend):

```powershell
docker compose up -d
```

This command will:
- Build the backend image from `backend/Dockerfile`
- Build the frontend image from `frontend/Dockerfile` (dev stage)
- Start PostgreSQL 17 at `localhost:5432` (user: `postgres`, password: `postgres`, database: `eitoap`)
- Start Redis 7 at `localhost:6379` for caching and rate limiting
- Start PgAdmin at `http://localhost:5050` for database management (admin@eitoap.local / adminpassword)
- Start the API Gateway at `http://localhost:8000` and modular backend services on ports 8001–8005
- Start the React frontend at `http://localhost:5173`

### 4. Wait for services to initialize

Check the status of running containers:

```powershell
docker compose ps
```

All services should show a status of "Up". If any container fails, check the logs:

```powershell
docker compose logs <service-name>
```

For example, to see backend logs:

```powershell
docker compose logs api-gateway
```

### 5. Run database migrations

Once the API Gateway is ready, run database migrations in a separate terminal:

```powershell
docker compose exec api-gateway alembic upgrade head
```

### 6. Access the application

- **Frontend:** Open <http://localhost:5173> in your browser
- **API Documentation:** Visit <http://localhost:8000/docs> for interactive Swagger documentation
- **Database Management:** Access PgAdmin at <http://localhost:5050>
- **Backend Microservices:**
  - Auth Service: <http://localhost:8001/docs>
  - Ticket Service: <http://localhost:8002/docs>
  - Workflow Service: <http://localhost:8003/docs>
  - Notification Service: <http://localhost:8004/docs>
  - Audit Service: <http://localhost:8005/docs>

### 7. View service logs

To stream logs from all services:

```powershell
docker compose logs -f
```

To follow logs from a specific service:

```powershell
docker compose logs -f frontend
docker compose logs -f api-gateway
docker compose logs -f postgres
```

### 8. Stop and clean up

To stop all services:

```powershell
docker compose stop
```

To stop and remove all containers:

```powershell
docker compose down
```

To also delete all stored data (irreversible):

```powershell
docker compose down --volumes
```

### Troubleshooting Docker Compose

| Issue | Solution |
| --- | --- |
| Port already in use | Change the port mapping in `docker-compose.yml` (e.g., `"8001:8001"` → `"8011:8001"`) and restart |
| Container crashes on startup | Check logs with `docker compose logs <service-name>` |
| Database connection errors | Ensure PostgreSQL is running and healthy: `docker compose logs postgres` |
| Frontend not connecting to API | Verify the `VITE_PROXY_TARGET` environment variable in `docker-compose.yml` matches the API Gateway URL |
| Out of memory | Increase Docker Desktop memory allocation and restart Docker |

---

## Run locally (manual setup)

### Prerequisites

- Git
- Python 3.12
- Node.js and npm

### 1. Clone the repository

```powershell
git clone https://github.com/utkarshstudent75-gif/entreprise-IT-Operations-automation-platform.git
Set-Location entreprise-IT-Operations-automation-platform
```

For your own deployment, fork the repository and clone your fork.

### 2. Configure local settings

```powershell
Copy-Item backend/.env.example backend/.env
```

In `backend/.env`, set `NOTIFICATION_PROVIDER=console`, keep PostgreSQL and Redis on `localhost`, and clear the example Entra ID/SMS placeholders unless you configured those integrations. These lo[...]

### 3. Start PostgreSQL and Redis

From the repository root:

```powershell
docker compose up -d postgres redis
```

### 4. Start the API

From the repository root:

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Keep this terminal open. The API is at <http://localhost:8000> and its interactive docs are at <http://localhost:8000/docs>.

### 5. Start the frontend

In a second terminal, from the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev -- --host 0.0.0.0
```

Open <http://localhost:5173>. Vite proxies API requests to `http://localhost:8000`.

To stop the database and cache containers, run `docker compose down` from the repository root. To also delete their stored data, run `docker compose down --volumes`; this is irreversible.

## Build the Docker images

Each image is built from its own Dockerfile and build context. Run these commands from the repository root with Docker running:

| Component | Dockerfile | Build context | Local image |
| --- | --- | --- | --- |
| Backend | [`backend/Dockerfile`](./backend/Dockerfile) | `backend/` | `eitoap-backend:local` |
| Frontend | [`frontend/Dockerfile`](./frontend/Dockerfile) | `frontend/` | `eitoap-frontend:local` |

```powershell
docker build -f backend/Dockerfile -t eitoap-backend:local ./backend
docker build -f frontend/Dockerfile --target production -t eitoap-frontend:local ./frontend
docker image ls eitoap-backend
docker image ls eitoap-frontend
```

These images are stored in your local Docker image store. The frontend build selects the Dockerfile's `production` stage, which serves the built app with unprivileged NGINX. To push your images t[...]

```powershell
az login
$acrName = "<your-acr-name>"
$acrLoginServer = "<your-acr-name>.azurecr.io"
az acr login --name $acrName

docker tag eitoap-backend:local "$acrLoginServer/backend:v1"
docker tag eitoap-frontend:local "$acrLoginServer/frontend:v1"
docker push "$acrLoginServer/backend:v1"
docker push "$acrLoginServer/frontend:v1"
```

## Deploy to Azure

The Azure development deployment uses Terraform for infrastructure, GitHub Actions to publish images, and Argo CD to deploy them. Azure resources can incur charges. Use a non-production subscript[...]

### 1. Prepare your fork and tools

Install Azure CLI, Terraform, `kubectl`, Helm, Docker, Git, and `jq`. The recommended bootstrap shell is Bash on Linux, macOS, or WSL; `gh` (GitHub CLI) is optional for automating GitHub configur[...]

Fork this repository. The current workflow and Argo CD manifests use the `master` branch. Keep that branch, or consistently update the branch in the workflow, GitOps settings, and manifests under[...]

### 2. Review Azure security and cost

The current development Terraform configuration creates a Windows validation VM with a public IP and allows RDP from `*`. **Before provisioning**, change `allowed_inbound_rdp_ips` in `infrastruct[...]

AKS nodes, the VM, databases, Redis, load balancers, and monitoring storage can incur charges. Check your regional quota and expected cost before applying.

### 3. Configure and run bootstrap

From the repository root, copy the bootstrap example and edit the project, region, environment, GitHub repository, and OIDC branch settings:

```bash
cp bootstrap/.env.example bootstrap/.env
```

Sign in to Azure and, if you want the script to configure GitHub automatically, GitHub CLI:

```bash
az login
gh auth login
bash bootstrap/bootstrap.sh
```

Review the selected subscription and Terraform plan carefully before confirming the apply. Bootstrap creates the remote Terraform state, configures an Azure identity for GitHub OIDC, and provisio[...]

Keep `bootstrap/.bootstrap-output.json` safe until teardown. It contains sensitive deployment metadata used by the cleanup helper; do not commit or share it. If you are using Windows without Bash[...]

### 4. Configure GitHub Actions

In **GitHub → Settings → Secrets and variables → Actions**, configure:

**Repository secrets**

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

**Repository variables**

- `ACR_NAME` — ACR registry name, without `.azurecr.io`
- `ACR_LOGIN_SERVER` — ACR login server, such as `myregistry.azurecr.io`

The bootstrap helper writes available values as **secrets**; the workflow reads `ACR_NAME` and `ACR_LOGIN_SERVER` as **variables**, so add or verify those two variables separately. Allow GitHub A[...]

Push a change to `master` to run CI and publish images. Pull requests and feature branches run checks but do not publish images. The `master` workflow publishes both images with the commit SHA an[...]

### 5. Install ingress and Argo CD

After bootstrap completes, install the NGINX ingress controller (not installed by Terraform):

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace --wait
```

After the first CI run publishes the images, install Argo CD and apply the root Application:

```bash
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl rollout status deployment/argocd-server -n argocd --timeout=5m
kubectl apply -f deploy/argocd/root-app.yaml -n argocd
kubectl get applications -n argocd
kubectl get ingress -n frontend
kubectl get svc -n ingress-nginx
```

Wait for the Argo CD Applications to become `Synced` and `Healthy`. Use the ingress address shown by Kubernetes to reach the frontend. The ingress uses an Azure LoadBalancer (which can incur char[...]

### 6. Install monitoring (optional)

Create the Grafana password Secret and install the observability chart:

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
kubectl get pods -n monitoring
```

Port-forward Grafana and Prometheus from separate terminals with `kubectl port-forward -n monitoring svc/grafana 3000:80` and `kubectl port-forward -n monitoring svc/prometheus 9090:9090`. Open <[...]

### 7. Verify and clean up

Run `bash bootstrap/verify.sh` to check Azure resources, Kubernetes connectivity, workload rollouts, and application readiness. Check Argo CD with `kubectl get applications -n argocd`.

When you are finished, run `bash bootstrap/cleanup.sh` and choose the full-environment teardown only if you intend to delete the Azure resources **and Terraform state**. Review and remove project[...]

## Repository layout

```text
backend/                  FastAPI app, tests, migrations, Dockerfile
frontend/                 React app, Dockerfile
deploy/helm/              Frontend, backend, common, and monitoring charts
deploy/argocd/            Argo CD applications
infrastructure/terraform/ Azure infrastructure
bootstrap/                Provisioning, verification, and cleanup scripts
docs/architecture/        Architecture diagram
docs/screenshots/         Selected project screenshots
```

See the [observability guide](./docs/phase-4-observability.md) for monitoring details. This project is licensed under the [MIT License](./LICENSE).
