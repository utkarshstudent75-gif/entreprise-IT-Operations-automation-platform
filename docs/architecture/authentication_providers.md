# Authentication & Enterprise Identity Foundation Architecture

This document describes the design and implementation details for the pluggable authentication architecture introduced in Sprint 3.

## Overview

The Enterprise IT Operations Automation Platform is designed to support multiple authentication methods:
- **Local Authentication**: Used primarily in local development, relying on credentials (email/username and password) stored in the PostgreSQL database, and verified using `bcrypt`.
- **Microsoft Entra ID (Azure AD)**: Used in enterprise deployments, relying on external identity verification using OpenID Connect (OIDC) via Microsoft Authentication Library (MSAL).

The backend isolates the authentication details using an **Authentication Provider Abstraction** pattern. The application depends only on the provider interface, avoiding Microsoft-specific logic throughout routers and application layers.

---

## Pluggable Architecture Design

The modular structure is located in the backend at `app/auth/`:

```text
app/
└── auth/
    ├── providers/
    │   ├── base.py       # BaseAuthenticationProvider Interface
    │   ├── local.py      # Local JWT Authentication implementation
    │   └── entra.py      # Microsoft Entra ID OIDC verification & mapping
    ├── jwt_validator.py  # Entra ID token signature & claim validator
    ├── dependencies.py   # FastAPI routes dependencies (auth & role authorization)
    ├── service.py        # Config-driven factory instantiating the active provider
    └── models.py         # Defined user roles
```

---

## Authentication Flow

### Local Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Browser
    participant FE as React Frontend
    participant BE as FastAPI Backend
    database DB as PostgreSQL Database

    User->>FE: Enters corporate email & password
    FE->>BE: POST /api/v1/users/login {username_or_email, password}
    BE->>DB: Query user by email or username
    DB-->>BE: User Record (with hashed_password)
    BE->>BE: Verify password using bcrypt (pwd_context)
    BE->>BE: Generate local JWT signed by JWT_SECRET_KEY
    BE->>DB: Write "user_login" SUCCESS event to audit log
    BE-->>FE: TokenResponse {access_token, user_details}
    FE->>FE: Store token in localStorage ('authToken')
    FE->>User: Redirects to /dashboard
```

### Microsoft Entra ID (OIDC) Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Browser
    participant FE as React Frontend
    participant MSAL as Azure MSAL Library
    participant Entra as Microsoft Entra ID
    participant BE as FastAPI Backend
    database DB as PostgreSQL Database

    User->>FE: Clicks "Sign in with Microsoft"
    FE->>MSAL: loginRedirect()
    MSAL->>Entra: OAuth2 authorization & consent flow
    Entra-->>MSAL: Return ID/Access Tokens
    MSAL-->>FE: Return authentication account details
    FE->>MSAL: acquireTokenSilent()
    MSAL-->>FE: Return ID token string
    FE->>FE: Store token in localStorage ('authToken')
    FE->>BE: GET /api/v1/tickets (Header Authorization: Bearer <ID_token>)
    BE->>BE: Extract token from authorization header
    BE->>BE: Retrieve JWKS from login.microsoftonline.com
    BE->>BE: Verify signature, issuer, audience, and exp
    BE->>DB: Query user by entra_oid (falls back to email)
    alt User is new
        BE->>DB: Create User {email, display_name, entra_oid, roles="HelpDesk", last_login}
    else User exists
        BE->>DB: Update User {display_name, entra_tenant_id, last_login}
    end
    BE-->>FE: Returns protected resources
    FE->>User: Renders Dashboard content
```

---

## User Mapping Configuration

When authenticating via Microsoft Entra ID, the backend maps properties to a local database user record. The local record is updated on every login. The mapping details are:

| Claim from Token | Database Column | Description |
| --- | --- | --- |
| `oid` (or `sub`) | `entra_oid` | Microsoft Entra Object ID (unique, indexed) |
| `name` | `display_name` | Full name of the user |
| `email` or `preferred_username` | `email` | Corporate email address |
| `tid` | `entra_tenant_id` | Microsoft Entra Tenant ID |
| (current timestamp) | `last_login` | Track user access history |

---

## Role-Based Access Control (RBAC)

The application supports roles to restrict access to secure administrative endpoints:
- **Admin**: Full system control. Can access `/admin` and `/audit-logs`.
- **HelpDesk**: Basic operator.
- **HR**: Human resources workflows.
- **Auditor**: Read-only audit logs access. Can access `/audit-logs`.

Route protection is implemented using the FastAPI dependency helper `require_roles`:

```python
# Restricts access to Admin role only
@router.get("/admin")
async def get_admin(current_user = Depends(require_roles("Admin"))):
    ...
```

---

## Environment Variables

### Backend Environment Configuration (`.env`)

```ini
# Provider Choice: local or entra
AUTH_PROVIDER=local

# Local JWT Configuration
JWT_SECRET_KEY=secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Microsoft Entra ID Configuration
ENTRA_TENANT_ID=common
ENTRA_CLIENT_ID=your-azure-app-client-id
ENTRA_REDIRECT_URI=http://localhost:5173
```

### Frontend Environment Configuration (`.env`)

```ini
# Provider Choice: local or entra
VITE_AUTH_PROVIDER=local

# Microsoft Entra ID Configuration
VITE_ENTRA_CLIENT_ID=your-azure-app-client-id
VITE_ENTRA_TENANT_ID=common
```

---

## Developer Setup Instructions

### Local Authentication Mode
1. In `backend/.env` and `frontend/.env`, set `AUTH_PROVIDER=local` and `VITE_AUTH_PROVIDER=local`.
2. Start PostgreSQL, Redis, and backend/frontend applications.
3. Access the portal at `http://localhost:5173/login`.
4. Fill in local credentials to authenticate.

### Microsoft Entra ID Mode
1. In `backend/.env` and `frontend/.env`, set `AUTH_PROVIDER=entra` and `VITE_AUTH_PROVIDER=entra`.
2. Configure `ENTRA_CLIENT_ID` and `VITE_ENTRA_CLIENT_ID` to match your Entra App registration.
3. Open the portal. The login screen will dynamically render the corporate "Sign in with Microsoft" button.
4. Perform sign-in using your Azure credentials.
