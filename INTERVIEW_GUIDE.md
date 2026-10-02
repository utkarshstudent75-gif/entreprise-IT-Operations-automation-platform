# EITOAP — Project Interview Guide

Use this as a speaking guide, not a script. Replace the ownership prompts with work you personally did; the repository alone does not prove individual contribution, production use, or business impact.

## 1. The project in one sentence

**EITOAP is a self-service IT operations portal that lets employees request common help-desk actions—such as password resets, account help, software, and tickets—while demonstrating how to build, secure, deploy, and monitor a cloud-hosted application.**

## 2. Interview-ready project explanations

### 30-second version

“I worked on an IT operations self-service platform. Employees use a React and TypeScript portal to submit requests, and a FastAPI backend handles authentication and request workflows, storing application data in PostgreSQL. The project also demonstrates an Azure delivery platform: GitHub Actions validates the app and infrastructure, builds container images, publishes versioned images to ACR, and updates Helm configuration in Git. Argo CD detects that Git change and reconciles the application into AKS. Prometheus and Grafana provide metrics and dashboards. It is a portfolio/demo project, so I distinguish implemented capabilities from production-proven outcomes.”

### 90-second version

“The problem is that routine IT tasks often require manual help-desk interaction. EITOAP provides a single portal for common requests—including password resets with OTP verification, tickets, software requests, notifications, and audit records. The frontend is React/TypeScript; the backend is a modular FastAPI application with PostgreSQL for persistent data and Redis configured for runtime connectivity and supporting services.

“For delivery, pull requests and pushes run CI checks. Backend and frontend validation run in parallel, followed by security and infrastructure/chart validation. Docker builds frontend and backend images. On a push to `master`, the images are pushed to Azure Container Registry with the commit SHA, and CI updates the development Helm values in Git. Argo CD watches that Git state and syncs Helm releases to AKS; CI does not directly apply manifests to the cluster. Prometheus and Grafana are included for metrics and dashboards.

“The main design distinction is that AKS runs a frontend and a modular backend—not a separate microservice for every feature. I’d describe this as a practical self-service app plus a GitOps/DevOps demonstration, and I’d be clear about remaining gaps such as the in-memory rate limiter and lack of frontend automated tests.”

### Explain the request and release flows

**User request:** Browser UI → API request to FastAPI → validation/business logic → PostgreSQL for durable records; Redis is configured and used by runtime support code. OTP/notification and audit behavior depend on the selected provider/configuration.

**Code to cluster:** Pull request/push → CI quality/tests/security/config validation → Docker images → (on `master` push) ACR images tagged with commit SHA → CI commits that SHA to dev Helm values → Argo CD detects desired-state change → Helm resources reconciled in AKS → Kubernetes probes and monitoring help verify operation.

## 3. Architecture and technology at a glance

| Layer | What to say |
|---|---|
| UI | React, TypeScript, Vite, Material UI; public auth/reset and protected request/dashboard pages. |
| API | Python 3.12, FastAPI, Pydantic, Uvicorn; modular routes/services for auth, password reset, tickets, workflows, software requests, audit, and related operations. |
| Persistence | PostgreSQL with SQLAlchemy and Alembic migrations. |
| Supporting services | Redis is part of the runtime/deployment configuration. **The current rate limiter uses a thread-safe in-memory store**, so its counters are per process rather than shared across replicas. |
| Packaging / local development | Separate frontend/backend Docker images; Docker Compose supports local services. |
| Cloud / deployment | Azure, Terraform, AKS, ACR, Helm, Argo CD; GitOps desired state is in the repository. |
| Observability | Prometheus/Grafana charts and Azure Monitor/Log Analytics infrastructure components. |
| Security checks | Ruff/Black/isort, Bandit, Semgrep, npm audit, Trivy, optional Cosign signing; Kubernetes secrets/Key Vault integration is represented in deployment configuration. |

**Deployment model:** The AKS app is two application workloads (frontend and modular backend), with supporting infrastructure/services. Do not describe the backend feature modules or legacy Compose service names as independently deployed AKS microservices.

## 4. CI/CD pipeline: exact story

Primary workflow: [`.github/workflows/ci.yml`](./.github/workflows/ci.yml).

1. **Triggers:** Pushes and pull requests targeting `master` or `feature/**`, plus manual `workflow_dispatch`. New runs cancel older overlapping runs on the same ref.
2. **Backend job:** Python 3.12 with PostgreSQL 17 and Redis 7 service containers; installs hash-pinned test dependencies; runs Ruff, Black, isort, Bandit, service-connectivity checks, pytest, and an app-import check. The regular test run excludes live SMS; that integration test runs only when SMS credentials are configured. Test/coverage/security reports are uploaded.
3. **Frontend job:** Node 22 and `npm ci`; npm audit is explicitly non-blocking; ESLint, TypeScript check, and production build run. There is no frontend unit/browser-test command declared in `frontend/package.json`.
4. **Security and deployment validation:** Semgrep follows backend/frontend. Helm lints and renders the common/backend/frontend charts. Terraform checks formatting and validates dev/prod configurations; **this CI job does not plan or apply infrastructure**.
5. **Container build:** Docker builds backend and frontend images after application checks, Semgrep, Helm, and Terraform pass. Both are built on eligible runs; only a push to `master` authenticates to Azure and pushes `latest` and commit-SHA tags to ACR. Images are also saved as artifacts for scanning.
6. **Image security / supply chain:** Trivy scans the repository filesystem for critical findings and scans the built images. High/critical image findings are reported in SARIF without failing that reporting step; unfixed critical image findings fail the job. CycloneDX SBOMs are generated. Cosign signs images on an eligible `master` push only when its private-key secret is configured.
7. **GitOps promotion to dev:** After Docker, Trivy, and signing jobs, an eligible push to `master` writes the commit SHA into `deploy/helm/values/dev.yaml` and pushes a GitOps commit. The workflow skips its own `chore(gitops): deploy ...` commits to avoid a loop. This automation updates **dev**, not a demonstrated staged dev→prod promotion.
8. **Cluster reconciliation:** The Argo CD root Application watches the repository and uses automated sync, prune, and self-heal. Argo CD applies the declared Helm releases to AKS. CI updates Git; Argo CD, not CI, reconciles the cluster.

There is also a separate **manual-only** validation-workstation lifecycle workflow (`.github/workflows/validation.yml`) using Azure OIDC for deploy/destroy actions. It is not the normal application release pipeline.

## 5. Likely interview questions and answer frameworks

### Recruiter / behavioral

**“What problem does it solve?”**  
“It centralizes common employee IT requests in a self-service portal and demonstrates the application and delivery workflow behind those requests. I would not claim measured ticket reduction or user adoption without data.”

**“What was your contribution?”**  
State only what you personally implemented. Use: “I owned **[specific component/change]**. The problem was **[context]**; I chose **[approach]** because **[reason]**; I validated it with **[tests/demo/CI]**. The result was **[verifiable outcome]**.” Do not imply sole authorship of the whole repository.

**“What was difficult, and what did you learn?”**  
Choose a real example you can defend (e.g. getting GitOps image tags, cloud identity, app configuration, or tests aligned). Explain the failure, diagnosis, fix, and proof. Avoid inventing an outage or quantified impact.

**“Why this project / what would you improve?”**  
Highlight the combination of application engineering and repeatable delivery. Improvements: distributed rate limiting, frontend automated tests, explicit environment promotion/rollback, stronger security defaults, and operational SLO evidence.

### Hiring manager / application design

**“Why a modular backend instead of microservices?”**  
“The current deployment is a frontend and a modular FastAPI backend. Keeping related features in one backend avoids extra network boundaries and operational overhead for this project. I would split a module only if independent scaling, ownership, release cadence, or fault isolation justified the added complexity.”

**“Walk through password reset.”**  
Describe the implemented API/service flow you can demonstrate: request verification → issue/send OTP → verify OTP within configured expiry/attempt limits → complete reset → record relevant audit outcome. Mention the configured OTP controls and point to the actual route/service/tests. Do not claim a control (e.g. distributed throttling or secure OTP storage) unless you have verified its implementation.

**“How do you handle persistence and schema changes?”**  
“PostgreSQL stores application records; SQLAlchemy provides the data layer and Alembic manages schema migrations. I run migrations before local use and include database-backed backend tests in CI.”

**“How do you handle failure or readiness?”**  
“The API has health endpoints and the AKS backend has startup, liveness, and readiness probes. CI checks PostgreSQL/Redis connectivity. I would still validate dependency-failure behavior, recovery, and end-to-end user impact before claiming production resilience.”

### Senior DevOps / platform

**“How does a change reach AKS?”**  
Give the 8-step CI/CD story above. Emphasize immutable SHA tags, Git as desired state, and Argo CD reconciliation.

**“What blocks the image/release?”**  
Backend lint/security/tests, frontend lint/type/build, Semgrep, Helm/Terraform validation, and critical Trivy gates are on the path to GitOps update. Be exact: npm audit and Trivy’s high/critical reporting step are non-blocking; optional Cosign signing only runs when configured.

**“How is infrastructure managed?”**  
“Terraform has reusable Azure modules and dev/test/prod environment configurations. CI formats and validates dev/prod; it does not apply them. Provisioning is a separate reviewed/bootstrap operation with remote state and Azure OIDC.”

**“How would you roll back?”**  
“Because image versions are SHA-tagged and Helm desired state is in Git, a rollback can revert the dev values commit to a known-good SHA and let Argo CD reconcile. I would verify database migration compatibility and app health; the repository does not demonstrate automated progressive delivery or a full production rollback policy.”

**“How do you scale and keep it available?”**  
“The backend chart supports multiple replicas, HPA, and a PDB; Kubernetes probes gate readiness and restart unhealthy pods. Actual capacity depends on configured resources and database/cache limits. The in-memory limiter is not consistent across replicas, so I’d move it to shared Redis before relying on it at scale.”

**“What do you monitor?”**  
“Prometheus/Grafana cover application/Kubernetes metrics and dashboards; Azure Monitor/Log Analytics components are included. I’d define actionable SLIs/SLOs, alert thresholds, and retention based on expected traffic before calling the setup production-operational.”

### Security / quality

**“How are credentials protected?”**  
“CI uses GitHub secrets and Azure OIDC rather than a long-lived Azure client secret; the deployment design references Key Vault for runtime secrets. I would verify the actual deployed identity/permissions and ensure no tracked values contain credentials. Secrets should be rotated if ever committed.”

**“What security controls are in CI?”**  
Name Bandit, Semgrep, npm audit, Trivy filesystem/image scans, SBOM generation, and optional Cosign signing. Explain their actual blocking behavior, not just tool names.

**“What is the biggest security/operations gap?”**  
“I would first review environment-specific configuration and secret handling, ensure ingress TLS and restricted network access, and replace the process-local rate limiter with a distributed implementation. The documented dev validation VM configuration warns that RDP must be restricted before provisioning; the ingress instructions also state TLS is not configured by default.”

**“How do you test?”**  
“Backend unit and integration tests cover core services and workflows with PostgreSQL/Redis in CI; SMS live integration is optional. Frontend CI checks lint, types, and production build, but no frontend unit/browser suite is declared. I’d add component/API contract and browser end-to-end tests around sign-in and high-risk request flows.”

## 6. Honest limitations and follow-up improvements

- **Demo, not proven production:** Do not invent active users, cost savings, uptime, SLOs, or incident history.
- **Rate limiter:** Current implementation is in-memory and per process; use an atomic Redis-backed limiter for consistent multi-replica enforcement.
- **Frontend confidence:** CI has lint/type/build checks but no declared frontend unit/E2E suite.
- **Promotion:** The normal pipeline updates dev Helm values only; Terraform validation is not an apply, and a complete environment-promotion/approval flow is not shown.
- **Security posture:** Audit tracked environment/Helm values for sensitive data; move secrets to Key Vault/managed identity and rotate any exposed credentials. Restrict the validation VM’s RDP source CIDR, configure TLS before sensitive ingress exposure, and review least-privilege permissions.
- **Supply chain:** Cosign is conditional, so signing is not guaranteed unless configured and verified; keep SHA references for traceability.

These are good answers when asked about trade-offs: identify the gap, explain its impact, propose a bounded fix, and say how you would verify it.

## 7. Demo / preparation checklist

Before an interview, be ready to:

- Draw browser → API → PostgreSQL/Redis and the CI → ACR → GitOps → Argo CD → AKS flow.
- Show one end-to-end feature and its tests; explain the request, validation, persistence, and audit/notification path.
- Show the workflow job graph and explain what fails versus what only reports.
- Explain a Helm value, a Terraform module/environment, an image SHA, and how Argo CD syncs it.
- Discuss one real contribution, one debugging story, and one improvement using evidence you personally know.
- Never share credentials, OTPs, private screenshots, or claim production impact without evidence.

## 8. Repository references

- Application and architecture overview / local setup: [`README.md`](./README.md)
- CI pipeline: [`.github/workflows/ci.yml`](./.github/workflows/ci.yml)
- Manual validation lifecycle: [`.github/workflows/validation.yml`](./.github/workflows/validation.yml)
- Backend routes, services, and tests: [`backend/app`](./backend/app), [`backend/tests`](./backend/tests)
- Frontend pages and scripts: [`frontend/src`](./frontend/src), [`frontend/package.json`](./frontend/package.json)
- Azure infrastructure: [`infrastructure/terraform`](./infrastructure/terraform)
- Helm charts and environment values: [`deploy/helm`](./deploy/helm)
- Argo CD root application: [`deploy/argocd/root-app.yaml`](./deploy/argocd/root-app.yaml)
- Architecture diagram: [`docs/architecture/eitoap-architecture.svg`](./docs/architecture/eitoap-architecture.svg)
