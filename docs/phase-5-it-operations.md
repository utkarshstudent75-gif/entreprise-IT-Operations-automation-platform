# Phase 5: IT Operations Automation

Phase 5 adds authenticated identity workflows and a software approval queue. It
reuses the existing FastAPI application, Entra ID JWT validation, role
dependencies, Microsoft Graph client, SQLAlchemy/Alembic database, audit
service, notification service, and Phase 4 observability instrumentation.

```text
Employee
   ↓
Frontend
   ↓
FastAPI
   ↓
RBAC
   ↓
Service Layer
   ├── Entra ID / Graph
   ├── PostgreSQL
   ├── Redis
   ├── Notification
   └── Audit
        ↓
     Observability
```

## Workflows

### Account unlock request

The authenticated employee submits their work email and a justification. The
API compares the submitted email with the validated Entra token identity before
storing a `PENDING` request. Employees can list their own requests; support
engineers and platform administrators can inspect the pending queue. Audit
events record the request without storing the justification in audit details.

Microsoft Graph v1.0 does not expose an operation to clear Entra Smart Lockout
or an on-premises Active Directory lockout. Setting `accountEnabled=true` is
not equivalent and could re-enable a deliberately disabled account. Therefore
this implementation deliberately does not mutate the account or claim an
unlock succeeded. An approved identity-management/AD unlock provider or
documented manual handling process is required to complete the request.
Authorized IT approvers can review the pending request queue in the unlock UI;
the platform does not send an automatic IT notification or mark manual work
complete.

### MFA reset

An authenticated employee confirms their own email address. The API verifies
it against the token identity, then calls Microsoft Graph to enumerate the
user's authentication methods and delete supported non-password methods.
Password authentication methods are never deleted. If Graph returns a method
type this service cannot safely delete, the operation stops and reports a safe
failure. Graph failures do not return raw Graph payloads or credentials.

The application registration needs the least Graph application permissions
necessary to read and delete supported authentication methods (for example,
`UserAuthenticationMethod.Read.All` and
`UserAuthenticationMethod.ReadWrite.All`, subject to tenant policy and Graph
permission requirements). Grant admin consent only after validating the
operations and target population in a test tenant.

### Software request and approval

An employee submits software name and business justification. The request is
stored as `PENDING`; employees can only see requests associated with their
validated token email. Platform administrators and support engineers can list
pending requests and approve or reject them. A conditional database update
changes the status only while it remains `PENDING`, so simultaneous or
duplicate decisions cannot produce multiple terminal outcomes.

On a decision, the service records the approver and decision timestamp, emits
an audit event, and sends an SMS notification to the requester's phone returned
by the existing Graph integration. If a phone destination or SMS delivery is
unavailable, the decision remains committed, the notification failure is
audited, and the API explicitly reports that the decision was saved but the
notification failed. Approval does not install software.

## API flow

All endpoints below are under `/api/v1` and require a valid bearer token:

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `POST` | `/identity/unlock-requests` | Employee or approver | Submit an identity-verified manual unlock request |
| `GET` | `/identity/unlock-requests/mine` | Employee or approver | List the caller's unlock requests |
| `GET` | `/identity/unlock-requests/pending` | Support engineer or platform administrator | Inspect unlock requests awaiting external/manual processing |
| `POST` | `/mfa/reset` | Employee or approver | Reset the caller's supported registered MFA methods |
| `POST` | `/software` | Employee or approver | Create a pending software request |
| `GET` | `/software/mine` | Employee or approver | List the caller's software requests |
| `GET` | `/software/pending` | Support engineer or platform administrator | List pending requests for review |
| `POST` | `/software/{id}/approve` | Support engineer or platform administrator | Approve a pending request |
| `POST` | `/software/{id}/reject` | Support engineer or platform administrator | Reject a pending request |

Responses use the existing `StandardResponse` envelope. Authentication is
handled by the existing `get_current_user` dependency. Submitted email values
for the unlock and MFA workflows must match the authenticated identity, and
the backend—not the frontend—enforces every role restriction.

## RBAC model

The existing Entra role mapping and `check_role` dependency are reused:

| Existing application role | Phase 5 capability |
|---|---|
| `Standard User` | Create software and unlock requests, view own requests, reset own MFA |
| `Support Engineer` | Employee capabilities plus pending queue access and approval decisions |
| `Platform Administrator` | Employee capabilities plus pending queue access and approval decisions |
| `Auditor` | No Phase 5 operations; existing audit read access remains unchanged |

Entra app roles `SoftwareRequestApprover`, `Approver`, and `Manager` map to the
existing `Support Engineer` application role. `ITAdmin` and `IT Admin` map to
`Platform Administrator`. This is a role mapping, not a new authorization
system.

## Database changes

Migration `ea52c816b741_add_phase5_operations` follows the existing Alembic
head. It does not edit prior migrations.

* `account_unlock_requests` stores the authenticated requester, a locally
  optional `users` relationship, justification, `PENDING` status, and
  timestamps. Indexes cover status, requester email, requester relationship,
  and the primary key.
* `software_requests` gains requester email, decision actor, decision note,
  and decision timestamp columns. Existing software request fields and table
  are reused; legacy rows remain valid because the added fields are nullable.

MFA reset is an immediate Graph operation and does not need a request table.

## Audit and notification

Phase 5 records these action names through the existing audit service:

* `account_unlock_requested`
* `mfa_reset`
* `software_request_created`
* `software_request_approved` / `software_request_rejected`
* `software_request_notification`

Audit details contain request identifiers, actor/requester email, software
name, outcome, and safe error codes. They never contain passwords, bearer
tokens, Graph access tokens, raw Graph responses, or MFA secret material.
Audit failures follow the existing Phase 4 audit service behavior.

Software decision SMS notifications reuse the existing Graph phone lookup and
notification provider. No phone number or SMS body is written to audit details.
Notification delivery is a post-commit side effect and is surfaced separately
from the persisted approval decision.

## Security considerations

* Entra token validation remains the sole authentication path. The email used
  for identity actions comes from validated claims and must match the submitted
  identity.
* RBAC is enforced server-side. Client route/sidebar restrictions are only a
  usability aid.
* Unlock requests cannot be used to probe arbitrary accounts: no target email
  is looked up in Graph, and a request for any other email than the caller's
  returns the same identity-verification failure.
* MFA reset is scoped to the caller. Password authentication methods are
  excluded, and unsupported Graph method types stop the reset rather than
  being reported as successfully cleared.
* Software decisions use an atomic `PENDING`-only transition. Completed
  requests cannot be changed.
* Audit and application logs avoid passwords, tokens, secrets, raw provider
  responses, and justification text.
* The Graph application identity should have only the permissions needed for
  these operations. Do not use `accountEnabled=true` as a substitute for
  account-unlock functionality.
* Software approval is a workflow decision only; endpointing or software
  installation is intentionally out of scope.

## Testing and validation

Run the Phase 5 integration tests from `backend`:

```powershell
pytest tests/integration/test_phase5_operations.py
```

Run all backend tests with:

```powershell
pytest
```

The tests cover identity verification, authorization failures, request
validation, Graph failures and success, own-request visibility, approver queue
visibility, approval/rejection, duplicate decisions, and notification
failures. Existing metrics and middleware remain registered by the existing
application bootstrap.

Frontend checks run from `frontend`:

```powershell
npm run lint
npm run build
```

Validate the migration without applying it to a live database:

```powershell
alembic upgrade head --sql
```

## Troubleshooting

* **401 Unauthorized**: acquire a fresh Entra access token and confirm it is
  sent as `Authorization: Bearer <token>`.
* **403 Forbidden**: confirm the validated token includes one of the
  configured employee/approver roles and that the submitted identity matches
  the caller.
* **MFA reset fails**: inspect the safe application error and Graph HTTP status
  in server logs; verify Graph application permissions/admin consent and check
  whether a new authentication method type needs explicit support.
* **Software decision reports notification failure**: the decision is already
  committed. Inspect `software_request_notification` audit status and verify
  the user's Graph phone information and SMS provider health before retrying
  notification through the operational process. Do not repeat the decision.
* **Unlock request remains pending**: this platform records and audits the
  request but does not clear Entra or on-premises lockout. Process it using the
  organization's approved identity-management channel.
