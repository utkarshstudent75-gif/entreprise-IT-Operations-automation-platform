# Enterprise IT Operations Automation Platform (EITOAP)

## Overview

The **Enterprise IT Operations Automation Platform (EITOAP)** is a cloud-native platform designed to automate repetitive enterprise IT helpdesk operations such as password resets, identity verification, ticket creation, notifications, and audit logging.

The project is being developed using modern **DevOps**, **Cloud Engineering**, and **Site Reliability Engineering (SRE)** practices. It follows a production-style development workflow with feature branches, containerization, CI/CD, Infrastructure as Code, and Kubernetes deployment.

The long-term goal is to build an enterprise-grade platform capable of integrating with **Microsoft Entra ID**, **Microsoft Graph API**, and **Microsoft Copilot Studio** to provide AI-powered IT self-service.

---

# Problem Statement

Enterprise IT helpdesks spend a significant amount of time performing repetitive Level 1 support tasks.

Typical workflow:

* User forgets password
* User contacts IT Helpdesk
* Technician verifies identity
* Password is reset manually
* Ticket is created
* User is notified
* Ticket is closed after confirmation

Although these tasks are repetitive and deterministic, they still consume valuable engineering time and increase operational costs.

---

# Solution

The Enterprise IT Operations Automation Platform automates the complete workflow by providing:

* Secure identity verification
* Password reset automation
* User self-service portal
* Microsoft Entra ID integration *(Planned)*
* Microsoft Graph API integration *(Planned)*
* Automatic ticket creation *(Planned)*
* Notification service
* Audit logging *(Planned)*
* AI-assisted support *(Future)*

---

# Project Goals

* Build an enterprise-grade cloud-native application.
* Demonstrate modern DevOps and Cloud Engineering practices.
* Showcase Infrastructure as Code.
* Implement secure and scalable application architecture.
* Build a portfolio-quality project suitable for technical interviews.
* Follow production engineering best practices.

---

# Technology Stack

## Frontend

* React
* TypeScript
* Vite

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

## Database

* PostgreSQL
* SQLAlchemy
* Alembic

## Cache

* Redis

## Containerization

* Docker
* Docker Compose

## Orchestration

* Kubernetes
* Minikube (Development)
* Azure Kubernetes Service (Production)

## Cloud

* Microsoft Azure

## Infrastructure as Code

* Terraform

## CI/CD

* GitHub Actions

## Identity *(Upcoming)*

* Microsoft Entra ID
* Microsoft Graph API

## Monitoring *(Upcoming)*

* Prometheus
* Grafana
* Azure Monitor
* OpenTelemetry

## AI *(Future)*

* Microsoft Copilot Studio

---

# Current Features

## Implemented

* FastAPI backend & React frontend implementation
* Forgot Password & OTP-based password reset workflow
* Notification service abstraction (with SMS delivery support)
* PostgreSQL integration with SQLAlchemy & Alembic migrations
* Redis caching & rate limiter integration
* Multi-stage Docker containerization and Docker Compose setup
* Production-ready Kubernetes manifests & Helm charts (backend, frontend, common)
* Terraform-managed Azure infrastructure (AKS, Postgres, Redis, ACR)
* CI/CD automation workflow (linting, image build/push via OIDC)

## Planned

* Monitoring & Observability (Prometheus, Grafana, OpenTelemetry, Azure Monitor)
* Microsoft Entra ID integration
* Microsoft Graph API integration

---

# High-Level Architecture

```text
                    Browser
                       │
                       ▼
                React Frontend
                       │
                  REST API Calls
                       │
                       ▼
                FastAPI Backend
```

### Target Production Architecture

```text
                        Users
                           │
                           ▼
                    Azure Load Balancer
                           │
                           ▼
                    Kubernetes (AKS)
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
    React Frontend                     FastAPI Backend
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
                 PostgreSQL                                     Redis
                       │
                       ▼
             Microsoft Graph API
                       │
                       ▼
                Microsoft Entra ID
```

---

# Repository Structure

```text
enterprise-it-operations-automation-platform/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
│
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── .dockerignore
│
├── deploy/
│   ├── helm/
│   └── kubernetes/
│
├── infrastructure/
│   └── terraform/
│
├── docs/
├── scripts/
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

# Running the Project

## Prerequisites

* Docker Desktop
* Docker Compose
* Git

## Clone the Repository

```bash
git clone https://github.com/<your-github-username>/entreprise-IT-Operations-automation-platform.git

cd entreprise-IT-Operations-automation-platform
```

## Build and Start the Application

```bash
docker compose up --build
```

## Application URLs

| Service            | URL                        |
| ------------------ | -------------------------- |
| Frontend           | http://localhost:5173      |
| Backend API        | http://localhost:8000      |
| FastAPI Swagger UI | http://localhost:8000/docs |

## Redis & Password Reset Architecture

The platform integrates **Redis 7** (using `redis:7-alpine`) to serve as the high-performance storage backend for the password reset workflow. Redis serves as the single source of truth for all temporary OTP states.

### Redis Key Design & Lifecycle
All Redis keys are centrally namespaced to prevent key collisions:
1. **Active OTP Hash (`otp:<email>`)**:
   - **Type**: Redis Hash
   - **Fields**: `otp_hash` (SHA-256 hash of the 6-digit OTP code) and `attempts` (count of failed verification attempts).
   - **TTL**: `settings.OTP_EXPIRY_MINUTES * 60` seconds (defaults to 5 minutes).
2. **Expiry Metadata Tracker (`otp:meta:<email>`)**:
   - **Type**: Redis String (`"1"`)
   - **TTL**: `settings.OTP_EXPIRY_MINUTES * 60 * 24` seconds (24 hours).
   - **Purpose**: Distinguishes between an expired OTP (meta key present, active key expired) and an invalid/non-existent request (neither key present).
3. **Consumed Anti-Replay Guard (`otp:used:<email>`)**:
   - **Type**: Redis String (`otp_hash`)
   - **TTL**: `settings.OTP_EXPIRY_MINUTES * 60` seconds.
   - **Purpose**: Prevents replay attacks by rejecting attempts to reuse a consumed OTP within the original expiration window.

### Security Controls
- **One-Way Hashing**: OTP values are never stored or logged in plaintext. They are hashed using SHA-256 before storing.
- **Secure Comparison**: OTP hashes are compared using constant-time string comparison (`secrets.compare_digest`) to prevent timing attacks.
- **Attempts Counter & Lockout**: Atomic increments (`hincrby`) track failed verification attempts. If `attempts >= settings.OTP_MAX_ATTEMPTS`, the OTP is immediately deleted from Redis and the user is locked out.
- **Immediate Consumption**: Upon successful password reset, the active OTP key is deleted immediately and marked in the anti-replay tracker.

---

## Environment Variables Configuration

The following table documents all environment variables used by the application backend. These are configured in the `backend/.env` file (copied from `backend/.env.example`).

| Variable Name | Description | Default Value | Example Value |
| --- | --- | --- | --- |
| **Database** | | | |
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL | N/A | `postgresql://postgres:postgres@localhost:5432/eitoap` |
| **Redis** | | | |
| `REDIS_URL` | Full Redis connection URL (overrides individual options if set) | N/A | `redis://localhost:6379/0` |
| `REDIS_HOST` | Hostname of the Redis server | `localhost` | `redis` |
| `REDIS_PORT` | Port of the Redis server | `6379` | `6379` |
| `REDIS_DB` | Redis database index | `0` | `0` |
| `REDIS_PASSWORD` | Optional password for Redis authentication | `""` | `mysecretpassword` |
| **OTP Settings** | | | |
| `OTP_LENGTH` | Length of generated OTP code | `6` | `6` |
| `OTP_EXPIRY_MINUTES` | Time limit in minutes for active OTP verification | `5` | `5` |
| `OTP_MAX_ATTEMPTS` | Maximum allowed failed attempts before OTP deletion | `3` | `3` |
| **SMS Notification** | | | |
| `NOTIFICATION_PROVIDER`| Notification dispatch provider (`console` or `sms`) | `console` | `sms` |
| `SMS_API_KEY` | Authentication API key for the third-party SMS provider | `""` | `sk_sms_0e3d6...` |
| `SMS_ACCOUNT_SID` | Twilio-style Account SID for the third-party SMS provider | `""` | `AC555682c8...` |
| `SMS_BASE_URL` | Endpoint URL of the third-party SMS API | `https://api.sms-provider.com/v1` | `https://od2.in/api/sms/send` |
| `SMS_SENDER_ID` | Sender name/number for dispatched SMS messages | `IT-OPS` | `+1234567890` |
| `SMS_TIMEOUT_SECONDS` | HTTP request timeout for SMS delivery requests | `5.0` | `5.0` |
| `SMS_RETRY_COUNT` | Number of times to retry transient SMS API failures | `3` | `3` |
| `SMS_TEST_RECIPIENT` | Fallback phone number used for OTP delivery when email is used | `""` | `+911800123456` |

---

## Testing Guide

The codebase enforces strict test coverage and static analysis verification. 

### Running Tests Locally
Ensure that the PostgreSQL and Redis containers are running:
```bash
docker compose up -d postgres redis
```

Navigate to the `backend` directory and run the test suite using pytest:
```bash
cd backend
.venv/bin/pytest --cov=app --cov-report=xml --cov-report=html --junitxml=junit.xml
```

This command runs the full test suite and automatically generates:
1. **Console Report**: Printed directly in the shell terminal.
2. **JUnit XML Report**: Created at `junit.xml` (useful for CI/CD integrations).
3. **Coverage XML**: Created at `coverage/coverage.xml`.
4. **Coverage HTML**: Generated in the `coverage/html/` directory (open `coverage/html/index.html` in a web browser to view).

### Security Analysis Scan
Run Bandit to check for common security bugs:
```bash
.venv/bin/bandit -r app -f json -o bandit-report.json
```
This generates a `bandit-report.json` detailing any identified vulnerabilities or security alerts.

---

## CI/CD Pipeline & GitHub Actions Strategy

The project utilizes GitHub Actions for continuous integration. The pipeline configuration is located in `.github/workflows/ci.yml`.

### Workflow Services
For the backend test job, the workflow automatically runs containerized service dependencies:
- **PostgreSQL**: Starts `postgres:17-alpine` database.
- **Redis**: Starts `redis:7-alpine` caching database.

### Workflow Steps
1. **Formatting & Linting**: Runs `ruff check .`, `black --check .`, and `isort --check .`.
2. **Security Scan**: Runs `bandit -r app` to find security vulnerabilities.
3. **Connectivity Wait**: Executes `python scripts/wait_for_services.py` to block until PostgreSQL and Redis are fully online, failing immediately if they are unreachable.
4. **Pytest Run**: Executes the test suite and generates `junit.xml` and coverage files.
5. **App Validation**: Validates the application imports cleanly via `python -c "from app.main import app"`.
6. **Docker Build & Trivy Scan**: Builds frontend and backend Docker images, saves them to `.tar` files, and scans them using `trivy` for high and critical OS/library vulnerabilities.

### Published CI Artifacts
Upon workflow completion, the following artifacts are uploaded to the Actions run:
- `pytest-junit-xml`: JUnit XML test report.
- `coverage-xml`: Coverage XML document.
- `coverage-html`: Full interactive coverage HTML report.
- `bandit-report`: JSON-formatted Bandit vulnerability scan report.
- `trivy-sarif-reports`: Trivy vulnerability SARIF documents (also uploaded to GitHub Security center).
- `backend-sbom` / `frontend-sbom`: CycloneDX-formatted Software Bill of Materials (SBOM).

---

## SMS Notification Integration

The platform features an Enterprise SMS Notification delivery integration designed with strict **Clean Architecture**, **Dependency Inversion**, and **Data Privacy Guarantees**.

```text
PasswordResetService
        │
        ▼
NotificationService
        │
        ▼
NotificationProvider (Interface)
   ┌────┴───────────────────────────┐
   ▼                                ▼
ConsoleNotificationProvider     ThirdPartySmsNotificationProvider
                                    │
                                    ▼ (SmsRequest DTO ONLY)
                                Third-Party SMS API
```

### Architecture & Data Privacy Guarantees
- **Strict Dependency Inversion**: `PasswordResetService` only depends on `NotificationService`, which delegates to `NotificationProvider`. The core application has ZERO knowledge of SMS vendor HTTP payloads, authentication, or headers.
- **DTO Enforcement**: The SMS provider ONLY receives a minimal `SmsRequest` DTO containing `phone_number` and `message`. No domain objects (`User`, `Ticket`, `AuditLog`), Entra ID claims, emails, or credentials leave the application.
- **Minimal SMS Message Content**: Contains ONLY the OTP code and expiration notice.
- **Log Security & Masking**: Destination phone numbers are masked in logs (e.g. `+1*****4567`). API keys, Account SIDs, authorization headers, and raw credentials are NEVER logged.
- **Configuration & Fast Fail**: Configuration parameters (`NOTIFICATION_PROVIDER`, `SMS_API_KEY`, `SMS_ACCOUNT_SID`, `SMS_BASE_URL`, `SMS_TIMEOUT_SECONDS`, `SMS_RETRY_COUNT`) are validated during application initialization.
- **Transient Retry Policy**: Retries transient failures (HTTP 5xx, timeouts, 429 rate limit) with exponential backoff up to `SMS_RETRY_COUNT`. Non-transient errors (HTTP 400, 401, 403) fail fast without retrying.
- **Extensible**: Designed for future seamless migration to Azure Communication Services, Twilio, or AWS SNS without altering core application logic.


---

# Development Workflow

This repository follows a feature-branch workflow similar to enterprise software development.

```text
main
│
├── feature/docker
├── feature/postgresql
├── feature/redis
├── feature/cicd
├── feature/kubernetes
├── feature/azure-deployment
└── feature/monitoring
```

Each feature is developed independently, tested, and merged into `main` after completion.

---

# Project Roadmap

## ✅ Phase 1 – Foundation *(Current)*

Completed

* Project architecture
* FastAPI backend
* React frontend
* Password reset workflow
* OTP verification
* Docker containerization
* Docker Compose setup

In Progress

* PostgreSQL integration
* SQLAlchemy ORM
* Alembic migrations

---

## 🚧 Phase 2 – Cloud Native

* Redis
* GitHub Actions
* Azure Container Registry
* Kubernetes
* Helm
* Azure Kubernetes Service

---

## 🚧 Phase 3 – Site Reliability Engineering

* Prometheus
* Grafana
* OpenTelemetry
* Azure Monitor
* Logging
* Metrics
* Alerting
* Dashboards

---

## 🚧 Phase 4 – AI Operations

* Microsoft Copilot Studio
* AI-powered IT Assistant
* Intelligent Ticket Routing
* Knowledge Base Search
* Root Cause Analysis

---

# Future Enhancements

* Account Unlock
* MFA Reset
* VPN Troubleshooting
* Software Requests
* Printer Support
* Manager Approval Workflow
* IT Analytics Dashboard
* Multi-Tenant Support

---

# Learning Objectives

This project demonstrates practical experience with:

* Python
* FastAPI
* React
* TypeScript
* Docker
* Docker Compose
* PostgreSQL
* Redis
* Kubernetes
* Microsoft Azure
* Terraform
* GitHub Actions
* DevOps
* Site Reliability Engineering (SRE)
* Infrastructure as Code
* CI/CD
* Cloud-native application architecture

---

# Current Status

**Version:** `v0.3.0`

### Completed

* ✅ FastAPI backend & React frontend implementation
* ✅ PostgreSQL integration with SQLAlchemy & Alembic migrations
* ✅ Redis caching & rate limiter integration
* ✅ Multi-stage Docker containerization and Docker Compose setup
* ✅ Production-ready Kubernetes raw manifests (`deploy/kubernetes/`)
* ✅ Reusable, parameterized Helm Charts (`deploy/helm/`)
* ✅ Production AKS infrastructure (Phase 3 Terraform deployment)
* ✅ CI/CD pipeline automation (Helm linting & secure OIDC ACR push)

---

# Kubernetes & Helm Architecture

This application is fully modernized and prepared for production-grade deployment to Azure Kubernetes Service (AKS), while maintaining 100% backward compatibility with local Docker Compose development.

## 1. Kubernetes Manifests (`deploy/kubernetes/`)
The raw Kubernetes resources are organized under `deploy/kubernetes/` and include:
- **`namespaces.yaml`**: Establishes the `eitoap` isolated namespace.
- **`configmaps.yaml`**: Outlines non-sensitive environment configurations for `frontend` and `backend`.
- **`secrets-template.yaml`**: Provides templates for database connections, API keys, and JWT keys.
- **`ingress.yaml`**: Configures NGINX Ingress routing rule where `/api` points to the backend API and all other paths `/` point to the Nginx frontend.
- **`backend/`**:
  - [deployment.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/deployment.yaml): FastAPI deployment running 2 replicas, configured with non-root security context, read-only root filesystem with a `/tmp` mount, and CPU/Memory requests and limits (`100m-500m` / `128Mi-256Mi`). Includes liveness, readiness, and startup probes targeting `/liveness` and `/readiness`.
  - [service.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/service.yaml): Exposes the backend inside the cluster on port `8000`.
  - [hpa.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/hpa.yaml): Horizontal Pod Autoscaler targeting 80% CPU/Memory utilization, scaling from 2 to 5 replicas.
  - [pdb.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/pdb.yaml): Pod Disruption Budget ensuring a minimum of 1 backend pod is available during node maintenance.
  - [network-policy.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/network-policy.yaml): Restricts inbound traffic to the backend, allowing ingress only from the frontend pods and ingress controllers.
- **`frontend/`**:
  - [deployment.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/deployment.yaml): Nginx frontend deployment running 2 replicas, utilizing a non-root unprivileged Nginx image, read-only filesystem with emptyDir cache mounts, and liveness/readiness probes.
  - [service.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/service.yaml): Exposes the frontend inside the cluster on port `80`.
  - [hpa.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/hpa.yaml): Configures CPU/Memory autoscaling from 2 to 5 replicas.
  - [pdb.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/pdb.yaml): Protects frontend availability during disruptions.
  - [network-policy.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/network-policy.yaml): Protects the frontend and allows traffic to backend.
- **`redis/`**:
  - [deployment.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/redis/deployment.yaml) & [service.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/redis/service.yaml): Deploy a secure single-replica caching layer inside the cluster.

## 2. Helm Charts (`deploy/helm/`)
To support reproducible multi-environment package management, raw manifests are compiled into reusable Helm charts under `deploy/helm/`:
- **`deploy/helm/common`**: Packages shared infrastructure assets such as configuration maps, secrets, and Redis caching.
- **`deploy/helm/backend`**: Packages the FastAPI application, its scaling policies (HPA, PDB), and security/networking rules.
- **`deploy/helm/frontend`**: Packages the React static asset server and the Nginx Ingress routing layer.
All environment secrets and endpoints are parameterized via `values.yaml` to ensure zero hardcoding.

## 3. AKS-Ready Improvements
- **Decoupled Configuration**: Database and Redis hosts are read dynamically from environment variables. The hostname fallback checks are updated (`not os.path.exists("/.dockerenv") and not os.environ.get("KUBERNETES_SERVICE_HOST")`) to ignore Kubernetes runtimes and preserve local developer setups.
- **Dynamic Ingress Proxy**: Vite dev server proxies `/api` to the backend locally, while the Kubernetes Ingress routes it directly in the cloud. This avoids compiling hostnames into frontend docker images.
- **Production Performance**: Disabled Python reload flags in the `entrypoint.sh` for production runs.
- **Structured JSON Logging**: Automatically switches logging to Structured JSON format in production and retains colored human-readable text logs in local development.
- **CI/CD Automation**: Updated `.github/workflows/ci.yml` to lint Helm charts and build/push production images to Azure Container Registry using Azure OIDC workload identities.

---

# Microsoft Entra ID SSO & Dashboard Architecture

We have integrated Microsoft Entra ID authentication and Microsoft Graph reset capabilities, introducing an authenticated Enterprise Dashboard alongside the public SSPR flow.

## 1. Separate Application Entry Points

The application is architecturally partitioned into two strict security zones:
1. **Public Zone (Anonymous):** Includes SSPR email submission, OTP code verification, Graph-mediated SSPR password submission, and portal login. Accessible without authentication.
2. **Authenticated Zone (SSO Protected):** Includes the dashboard, My Profile, Session Info, Reset History, and security notifications. Accessible only after valid Microsoft Entra ID authentication.

## 2. Authentication Flow

The SSO login relies on **MSAL React (MSAL v3)** implementing the OpenID Connect (OIDC) **Authorization Code Flow with PKCE**:

```mermaid
sequenceDiagram
    participant User as User Browser
    participant MSAL as React MSAL Client
    participant Entra as Microsoft Entra ID
    participant Backend as FastAPI Backend
    
    User->>MSAL: Click "Sign In with Microsoft"
    MSAL->>Entra: Authorization Request + Code Challenge (PKCE)
    Entra->>User: Authenticate & Request Consent
    User->>Entra: Provide Credentials
    Entra->>MSAL: Auth Code Redirect
    MSAL->>Entra: Swap Code + Verifier for Tokens
    Entra->>MSAL: ID & Access Token
    MSAL->>Backend: Request APIs (Bearer Access Token)
    Backend->>Backend: Validate Token Signature/Audience/Claims
    Backend->>User: Return Restricted Data
```

*   **Silent Token Refresh:** MSAL React automatically renews the token silently in the background before it expires, using session storage claims.
*   **Developer Mock SSO Bypass:** If `ENTRA_CLIENT_ID` is not configured, the frontend renders a mock selector. Clicking a role requests a locally signed JWT token from `/users/mock-token` (signed using `JWT_SECRET_KEY`) which mimics Entra ID OIDC claims (`preferred_username`, `name`, `roles`).

## 3. Backend JWT Validation

The backend executes secure, stateless signature checks on every Bearer token:
- **JWKS Key Caching:** Fetches public keys from the tenant's OIDC discovery endpoint (`discovery/v2.0/keys`) and caches them in memory for 12 hours.
- **Claims Verification:** Asserts signature validity (RS256), audience matches `ENTRA_CLIENT_ID`, issuer matches the active tenant (`https://login.microsoftonline.com/{tenant}/v2.0`), and the token is not expired.
- **Fallback Verification:** If in developer mock mode, validates HS256 signature against local `JWT_SECRET_KEY`.

## 4. Role-Based Access Control (RBAC)

FastAPI endpoints and React frontend routes are restricted based on security privilege mappings decoded from the token's `roles` claims:
- **`Platform Administrator`**: Administrative configuration, full log auditing, user management.
- **`Support Engineer`**: Access to identity helpdesk tools (MFA reset, password resets, account unlocking).
- **`Auditor`**: Read-only log viewing and session monitoring.
- **`Standard User`**: Base profile access and self-service history details.

## 5. Security & Rate Limiting

- **SSPR Brute-Force Protection:** If an email or IP address fails SSPR verification 5 times, it is placed on a **15-minute Redis-based cooldown block**. Any requests during this period are rejected with `HTTP 429 Too Many Requests`.
- **Password Complexity Policy:** Enforces complexity criteria both in frontend UI (live checkbox requirements) and backend schemas (minimum length of 12, uppercase, lowercase, numbers, special characters, and weak blacklist dictionary checks).

## 6. Microsoft Graph Integration & Key Vault Configuration

The SSPR workflow uses the Microsoft Graph API to securely look up corporate accounts and perform password resets. The backend supports loading credentials and connection settings directly from environment variables or dynamically from **Azure Key Vault** using **Azure Workload Identity**.

### Environment Variables
Configure the following variables in your `.env` or Kubernetes ConfigMap/Secret:
- `TENANT_ID` / `ENTRA_TENANT_ID`: Microsoft Entra tenant ID (Directory ID).
- `CLIENT_ID` / `ENTRA_CLIENT_ID`: App registration Application (Client) ID.
- `CLIENT_SECRET` / `ENTRA_CLIENT_SECRET`: App registration Client Secret.
- `GRAPH_SCOPES`: Customizable scopes for the MS Graph access token (default: `https://graph.microsoft.com/.default`).
- `KEYVAULT_NAME`: Name of the Azure Key Vault to dynamically retrieve configuration secrets.

### Required Microsoft Graph API Permissions
Ensure the Application Registration has the following **Application** permissions granted under **API Permissions** -> **Microsoft Graph**:
- `User.ReadWrite.All`: Required to look up users and reset passwords.
- **Admin Consent**: Ensure a Tenant Administrator clicks **Grant admin consent** for the tenant.

### Azure Key Vault Secret Mappings
When `KEYVAULT_NAME` is configured, the application retrieves the following secret names from Key Vault on startup:
- `msgraph-client-id`: Client ID override
- `msgraph-client-secret`: Client Secret override
- `msgraph-tenant-id`: Tenant ID override
- `database-host`, `database-name`, `database-port`, `database-username`, `database-password`: Reconstructs the DB connection URL
- `redis-host`, `redis-port`, `redis-primary-key`: Reconstructs the Redis connection URL
- `sms-provider-api-key`, `sms-provider-account-sid`: Notification keys

### Local Development vs Azure Deployment
- **Local Development**: Leave `KEYVAULT_NAME` unset or empty. The backend will fall back to local `.env` variables or standard defaults.
- **Azure Deployment (AKS)**: Deploy AKS with Workload Identity enabled. Associate the backend `ServiceAccount` with the Azure User-Assigned Managed Identity. Set `KEYVAULT_NAME` to your vault name. The container will authenticate passwordlessly to the Key Vault using `DefaultAzureCredential` to fetch all database, Redis, and Microsoft Graph secrets.

* Dashboards

---

## 🚧 Phase 4 – AI Operations

* Microsoft Copilot Studio
* AI-powered IT Assistant
* Intelligent Ticket Routing
* Knowledge Base Search
* Root Cause Analysis

---

# Future Enhancements

* Account Unlock
* MFA Reset
* VPN Troubleshooting
* Software Requests
* Printer Support
* Manager Approval Workflow
* IT Analytics Dashboard
* Multi-Tenant Support

---

# Learning Objectives

This project demonstrates practical experience with:

* Python
* FastAPI
* React
* TypeScript
* Docker
* Docker Compose
* PostgreSQL
* Redis
* Kubernetes
* Microsoft Azure
* Terraform
* GitHub Actions
* DevOps
* Site Reliability Engineering (SRE)
* Infrastructure as Code
* CI/CD
* Cloud-native application architecture

---

# Current Status

**Version:** `v0.3.0`

### Completed

* ✅ FastAPI backend & React frontend implementation
* ✅ PostgreSQL integration with SQLAlchemy & Alembic migrations
* ✅ Redis caching & rate limiter integration
* ✅ Multi-stage Docker containerization and Docker Compose setup
* ✅ Production-ready Kubernetes raw manifests (`deploy/kubernetes/`)
* ✅ Reusable, parameterized Helm Charts (`deploy/helm/`)
* ✅ Production AKS infrastructure (Phase 3 Terraform deployment)
* ✅ CI/CD pipeline automation (Helm linting & secure OIDC ACR push)

---

# Kubernetes & Helm Architecture

This application is fully modernized and prepared for production-grade deployment to Azure Kubernetes Service (AKS), while maintaining 100% backward compatibility with local Docker Compose development.

## 1. Kubernetes Manifests (`deploy/kubernetes/`)
The raw Kubernetes resources are organized under `deploy/kubernetes/` and include:
- **`namespaces.yaml`**: Establishes the `eitoap` isolated namespace.
- **`configmaps.yaml`**: Outlines non-sensitive environment configurations for `frontend` and `backend`.
- **`secrets-template.yaml`**: Provides templates for database connections, API keys, and JWT keys.
- **`ingress.yaml`**: Configures NGINX Ingress routing rule where `/api` points to the backend API and all other paths `/` point to the Nginx frontend.
- **`backend/`**:
  - [deployment.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/deployment.yaml): FastAPI deployment running 2 replicas, configured with non-root security context, read-only root filesystem with a `/tmp` mount, and CPU/Memory requests and limits (`100m-500m` / `128Mi-256Mi`). Includes liveness, readiness, and startup probes targeting `/liveness` and `/readiness`.
  - [service.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/service.yaml): Exposes the backend inside the cluster on port `8000`.
  - [hpa.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/hpa.yaml): Horizontal Pod Autoscaler targeting 80% CPU/Memory utilization, scaling from 2 to 5 replicas.
  - [pdb.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/pdb.yaml): Pod Disruption Budget ensuring a minimum of 1 backend pod is available during node maintenance.
  - [network-policy.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/backend/network-policy.yaml): Restricts inbound traffic to the backend, allowing ingress only from the frontend pods and ingress controllers.
- **`frontend/`**:
  - [deployment.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/deployment.yaml): Nginx frontend deployment running 2 replicas, utilizing a non-root unprivileged Nginx image, read-only filesystem with emptyDir cache mounts, and liveness/readiness probes.
  - [service.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/service.yaml): Exposes the frontend inside the cluster on port `80`.
  - [hpa.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/hpa.yaml): Configures CPU/Memory autoscaling from 2 to 5 replicas.
  - [pdb.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/pdb.yaml): Protects frontend availability during disruptions.
  - [network-policy.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/frontend/network-policy.yaml): Protects the frontend and allows traffic to backend.
- **`redis/`**:
  - [deployment.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/redis/deployment.yaml) & [service.yaml](file:///home/utkarsh/projects/entreprise-IT-Operations-automation-platform/deploy/kubernetes/redis/service.yaml): Deploy a secure single-replica caching layer inside the cluster.

## 2. Helm Charts (`deploy/helm/`)
To support reproducible multi-environment package management, raw manifests are compiled into reusable Helm charts under `deploy/helm/`:
- **`deploy/helm/common`**: Packages shared infrastructure assets such as configuration maps, secrets, and Redis caching.
- **`deploy/helm/backend`**: Packages the FastAPI application, its scaling policies (HPA, PDB), and security/networking rules.
- **`deploy/helm/frontend`**: Packages the React static asset server and the Nginx Ingress routing layer.
All environment secrets and endpoints are parameterized via `values.yaml` to ensure zero hardcoding.

## 3. AKS-Ready Improvements
- **Decoupled Configuration**: Database and Redis hosts are read dynamically from environment variables. The hostname fallback checks are updated (`not os.path.exists("/.dockerenv") and not os.environ.get("KUBERNETES_SERVICE_HOST")`) to ignore Kubernetes runtimes and preserve local developer setups.
- **Dynamic Ingress Proxy**: Vite dev server proxies `/api` to the backend locally, while the Kubernetes Ingress routes it directly in the cloud. This avoids compiling hostnames into frontend docker images.
- **Production Performance**: Disabled Python reload flags in the `entrypoint.sh` for production runs.
- **Structured JSON Logging**: Automatically switches logging to Structured JSON format in production and retains colored human-readable text logs in local development.
- **CI/CD Automation**: Updated `.github/workflows/ci.yml` to lint Helm charts and build/push production images to Azure Container Registry using Azure OIDC workload identities.

---

# Microsoft Entra ID SSO & Dashboard Architecture

We have integrated Microsoft Entra ID authentication and Microsoft Graph reset capabilities, introducing an authenticated Enterprise Dashboard alongside the public SSPR flow.

## 1. Separate Application Entry Points

The application is architecturally partitioned into two strict security zones:
1. **Public Zone (Anonymous):** Includes SSPR email submission, OTP code verification, Graph-mediated SSPR password submission, and portal login. Accessible without authentication.
2. **Authenticated Zone (SSO Protected):** Includes the dashboard, My Profile, Session Info, Reset History, and security notifications. Accessible only after valid Microsoft Entra ID authentication.

## 2. Authentication Flow

The SSO login relies on **MSAL React (MSAL v3)** implementing the OpenID Connect (OIDC) **Authorization Code Flow with PKCE**:

```mermaid
sequenceDiagram
    participant User as User Browser
    participant MSAL as React MSAL Client
    participant Entra as Microsoft Entra ID
    participant Backend as FastAPI Backend
    
    User->>MSAL: Click "Sign In with Microsoft"
    MSAL->>Entra: Authorization Request + Code Challenge (PKCE)
    Entra->>User: Authenticate & Request Consent
    User->>Entra: Provide Credentials
    Entra->>MSAL: Auth Code Redirect
    MSAL->>Entra: Swap Code + Verifier for Tokens
    Entra->>MSAL: ID & Access Token
    MSAL->>Backend: Request APIs (Bearer Access Token)
    Backend->>Backend: Validate Token Signature/Audience/Claims
    Backend->>User: Return Restricted Data
```

*   **Silent Token Refresh:** MSAL React automatically renews the token silently in the background before it expires, using session storage claims.
*   **Developer Mock SSO Bypass:** If `ENTRA_CLIENT_ID` is not configured, the frontend renders a mock selector. Clicking a role requests a locally signed JWT token from `/users/mock-token` (signed using `JWT_SECRET_KEY`) which mimics Entra ID OIDC claims (`preferred_username`, `name`, `roles`).

## 3. Backend JWT Validation

The backend executes secure, stateless signature checks on every Bearer token:
- **JWKS Key Caching:** Fetches public keys from the tenant's OIDC discovery endpoint (`discovery/v2.0/keys`) and caches them in memory for 12 hours.
- **Claims Verification:** Asserts signature validity (RS256), audience matches `ENTRA_CLIENT_ID`, issuer matches the active tenant (`https://login.microsoftonline.com/{tenant}/v2.0`), and the token is not expired.
- **Fallback Verification:** If in developer mock mode, validates HS256 signature against local `JWT_SECRET_KEY`.

## 4. Role-Based Access Control (RBAC)

FastAPI endpoints and React frontend routes are restricted based on security privilege mappings decoded from the token's `roles` claims:
- **`Platform Administrator`**: Administrative configuration, full log auditing, user management.
- **`Support Engineer`**: Access to identity helpdesk tools (MFA reset, password resets, account unlocking).
- **`Auditor`**: Read-only log viewing and session monitoring.
- **`Standard User`**: Base profile access and self-service history details.

## 5. Security & Rate Limiting

- **SSPR Brute-Force Protection:** If an email or IP address fails SSPR verification 5 times, it is placed on a **15-minute Redis-based cooldown block**. Any requests during this period are rejected with `HTTP 429 Too Many Requests`.
- **Password Complexity Policy:** Enforces complexity criteria both in frontend UI (live checkbox requirements) and backend schemas (minimum length of 12, uppercase, lowercase, numbers, special characters, and weak blacklist dictionary checks).

## 6. Microsoft Graph Integration & Key Vault Configuration

The SSPR workflow uses the Microsoft Graph API to securely look up corporate accounts and perform password resets. The backend supports loading credentials and connection settings directly from environment variables or dynamically from **Azure Key Vault** using **Azure Workload Identity**.

### Environment Variables
Configure the following variables in your `.env` or Kubernetes ConfigMap/Secret:
- `TENANT_ID` / `ENTRA_TENANT_ID`: Microsoft Entra tenant ID (Directory ID).
- `CLIENT_ID` / `ENTRA_CLIENT_ID`: App registration Application (Client) ID.
- `CLIENT_SECRET` / `ENTRA_CLIENT_SECRET`: App registration Client Secret.
- `GRAPH_SCOPES`: Customizable scopes for the MS Graph access token (default: `https://graph.microsoft.com/.default`).
- `KEYVAULT_NAME`: Name of the Azure Key Vault to dynamically retrieve configuration secrets.

### Required Microsoft Graph API Permissions
Ensure the Application Registration has the following **Application** permissions granted under **API Permissions** -> **Microsoft Graph**:
- `User.ReadWrite.All`: Required to look up users and reset passwords.
- **Admin Consent**: Ensure a Tenant Administrator clicks **Grant admin consent** for the tenant.

### Azure Key Vault Secret Mappings
When `KEYVAULT_NAME` is configured, the application retrieves the following secret names from Key Vault on startup:
- `msgraph-client-id`: Client ID override
- `msgraph-client-secret`: Client Secret override
- `msgraph-tenant-id`: Tenant ID override
- `database-host`, `database-name`, `database-port`, `database-username`, `database-password`: Reconstructs the DB connection URL
- `redis-host`, `redis-port`, `redis-primary-key`: Reconstructs the Redis connection URL
- `sms-provider-api-key`, `sms-provider-account-sid`: Notification keys

### Local Development vs Azure Deployment
- **Local Development**: Leave `KEYVAULT_NAME` unset or empty. The backend will fall back to local `.env` variables or standard defaults.
- **Azure Deployment (AKS)**: Deploy AKS with Workload Identity enabled. Associate the backend `ServiceAccount` with the Azure User-Assigned Managed Identity. Set `KEYVAULT_NAME` to your vault name. The container will authenticate passwordlessly to the Key Vault using `DefaultAzureCredential` to fetch all database, Redis, and Microsoft Graph secrets.

### Troubleshooting
- **ModuleNotFoundError for 'azure'**: Make sure the packages `azure-identity` and `azure-keyvault-secrets` are installed (`pip install -r requirements.txt`).
- **GraphAPIException (INSUFFICIENT_PERMISSIONS)**: Microsoft Graph API does not allow application-level permissions to reset passwords of Administrative accounts (e.g. Global Administrators). Test resets on standard non-admin User accounts.
- **Key Vault Access Failure**: If Key Vault secret retrieval fails, verify that your Managed Identity or deployment principal has the **Key Vault Secrets User** role assignment on Key Vault.

---

# Enterprise Validation Workstation

The repository includes a complete Enterprise Validation Workstation configuration designed to simulate a real employee workstation. This dedicated environment is used for end-to-end platform validation, user acceptance testing (UAT), and portfolio demonstrations.

## 1. Validation Architecture
The validation workstation is deployed as a Windows 11 Enterprise Gen2 Virtual Machine in a dedicated subnet (`validation-subnet`) within the existing virtual network. 

```mermaid
graph TD
    A[Employee signs into Windows via Microsoft Entra ID] --> B[Windows Desktop Loads]
    B --> C[Edge Automatically Launches via Startup Batch Script]
    C --> D[Edge Navigates to http://portal.company.com/dashboard]
    D --> E{MSAL ssoSilent check}
    E -- Session Exists --> F[Seamless Single Sign-On into Dashboard]
    E -- Session Missing --> G[Redirect to Microsoft Entra login page]
    G --> H[User Authenticates]
    H --> F
```

## 2. Workstation Features
*   **Operating System:** Windows 11 Enterprise Gen2 (offers advanced security configurations).
*   **Trusted Launch:** Enabled with Secure Boot and vTPM for hardware-level integrity checks.
*   **Microsoft Entra ID Join:** Integrated via the `AADLoginForWindows` extension. Traditional domain controllers are not used. Users sign in using Microsoft Entra credentials.
*   **Automatic Browser Launch:** Installs a startup script in the all-users startup folder, launching Microsoft Edge to point to `http://portal.company.com/dashboard` upon desktop load.
*   **Single Sign-On (SSO):** Incorporates `ssoSilent` authentication within the React dashboard context. If silent token acquisition fails, it automatically triggers a page redirect to the Microsoft Entra login screen.
*   **Auto Shutdown:** Configured via Azure DevTest schedule to shut down the VM daily at 7:00 PM EST, minimizing idle computing cost.
*   **Pre-installed Software:** Bootstrapped via Chocolatey to include Microsoft Edge, PowerShell 7, Azure CLI, Git, VS Code, and the Azure Monitor Agent.

## 3. Provisioning Workstation
You can provision the VM automatically using the provided PowerShell script in the root directory:
```powershell
./scripts/Provision-ValidationVM.ps1
```
This script initializes Terraform in the `environments/dev` workspace, applies the plan, and outputs the VM Name, Public IP, and Private IP. The local administrator password is randomly generated and stored securely in Azure Key Vault as `validation-vm-admin-password`.

## 4. Connecting & Login
1.  Verify the VM has finished provisioning and has successfully executed the startup script (can take 5-10 minutes).
2.  Open your RDP client and target the **Public IP** of the workstation (Port 3389).
3.  Sign in using Microsoft Entra credentials:
    *   **Username:** `validation.employee@itproject.in`
    *   **Password:** (The password configured in your Microsoft Entra tenant for the user).
    *   *Note: If connecting via RDP with Entra ID, ensure your RDP client supports Network Level Authentication (NLA) and you use the credentials format `AzureAD\validation.employee@itproject.in`.*

## 5. Health Check & Validation
To verify the health of local workstation policies and remote infrastructure connectivity, run the health check script from the workstation or from a management node:
```powershell
./scripts/Invoke-HealthCheck.ps1 -ResourceGroupName "eitoap-dev-rg" -AksClusterName "enterprise-dev-aks"
```
This checks:
*   Local RDP & Clipboard registry settings.
*   Local timezone alignment.
*   Chocolatey, Git, VS Code, and Azure CLI installations.
*   AKS Cluster and Deployment Pod states.
*   Central API health, database, and Redis connectivity.

## 6. Teardown
To destroy the validation workstation resources and prevent billing charges, execute:
```powershell
./scripts/Destroy-ValidationEnvironment.ps1
```
This script targets only the validation VM, NIC, NSG, public IP, startup scripts, and role assignments to protect core AKS and database infrastructure from deletion.

## 7. Estimated Azure Cost

| Azure Resource | Size / Specification | Monthly Cost (Est. USD) | Cost Optimization Recommendation |
| :--- | :--- | :---: | :--- |
| **Windows 11 VM** | Standard_D2s_v5 (2 vCPUs, 8 GB RAM) | ~$75.00 | **Auto Shutdown:** Reduces active hours to ~160 hrs/month, dropping costs to **~$18.00/month**. |
| **Premium SSD Disk** | 128 GB Premium SSD | ~$19.20 | Delete OS disk when tearing down environment. |
| **Public IP Address** | Static Standard IP | ~$3.60 | Toggle `enable_public_ip` to `false` when using VPN. |
| **Total Cost** | **Active 24/7:** **~$97.80/month** | **With Auto-Shutdown:** **~$40.80/month** | |

---

# License

This project is licensed under the MIT License.
