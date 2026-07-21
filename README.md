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

## Redis Infrastructure

The platform integrates **Redis 7** (using `redis:7-alpine`) to serve as the high-performance storage backend for future sprints (OTP storage, caching, and rate limiting).

### Starting Redis Locally
Redis starts automatically as part of the local Docker Compose stack:
```bash
docker compose up -d
```

### Environment Variables
The application's Redis client is configured via the following environment variables (defined in `.env`):
- `REDIS_URL`: Full Redis connection URL (e.g., `redis://redis:6379/0`). If provided, this URL overrides individual host/port configurations.
- `REDIS_HOST`: Redis host name (defaults to `localhost`).
- `REDIS_PORT`: Redis port (defaults to `6379`).
- `REDIS_DB`: Redis database index (defaults to `0`).
- `REDIS_PASSWORD`: Optional Redis password.

### Readiness Health Check
The application health check system has been updated. The `/ready` (and `/api/v1/ready`) endpoint checks the status of both **PostgreSQL** and **Redis**. It returns a `503 Service Unavailable` response if either service is unreachable:
- Request: `GET /ready`
- Success Response (200 OK):
  ```json
  {
    "success": true,
    "data": {
      "status": "ready",
      "database": "connected",
      "redis": "connected"
    }
  }
  ```

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
