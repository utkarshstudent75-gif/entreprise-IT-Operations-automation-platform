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

## Database *(Upcoming)*

* PostgreSQL
* SQLAlchemy
* Alembic

## Cache *(Upcoming)*

* Redis

## Containerization

* Docker
* Docker Compose

## Orchestration *(Upcoming)*

* Kubernetes
* Minikube (Development)
* Azure Kubernetes Service (Production)

## Cloud *(Upcoming)*

* Microsoft Azure

## Infrastructure as Code *(Upcoming)*

* Terraform

## CI/CD *(Upcoming)*

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

* FastAPI backend
* React frontend
* Forgot Password workflow
* OTP verification
* Password reset workflow
* Notification service abstraction
* Dockerized backend
* Dockerized frontend
* Docker Compose development environment

## In Progress

* PostgreSQL integration
* SQLAlchemy ORM
* Database migrations

## Planned

* Redis
* GitHub Actions CI/CD
* Kubernetes deployment
* Azure deployment
* Monitoring & Observability
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
├── infrastructure/
│   ├── helm/
│   ├── kubernetes/
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

**Version:** `v0.2.0`

### Completed

* ✅ Backend implementation
* ✅ Frontend implementation
* ✅ Password reset workflow
* ✅ OTP verification
* ✅ Dockerized frontend
* ✅ Dockerized backend
* ✅ Docker Compose development environment
* ✅ End-to-end application successfully running inside Docker containers

### Currently Working On

* PostgreSQL integration
* SQLAlchemy ORM
* Alembic migrations

---

# License

This project is licensed under the MIT License.
