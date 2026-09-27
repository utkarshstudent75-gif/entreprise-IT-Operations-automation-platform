from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import jwt

from app.core.config import settings
from app.models.account_unlock_request import AccountUnlockRequest
from app.models.audit_log import AuditLog
from app.models.software_request import SoftwareRequest
from app.schemas.sms import SmsRequest
from app.services.graph_service import GraphAPIException, graph_service
from app.services.notification_service import notification_service


def token_headers(client, email: str, role: str = "Standard User") -> dict[str, str]:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "preferred_username": email,
            "name": email.split("@")[0],
            "roles": [role.replace(" ", "")],
            "aud": settings.ENTRA_CLIENT_ID or settings.CLIENT_ID or "MOCK_CLIENT_ID",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_account_unlock_request_records_verified_identity(client, db):
    email = "employee@example.com"
    headers = token_headers(client, email)

    response = client.post(
        "/api/v1/identity/unlock-requests",
        headers=headers,
        json={
            "email": email,
            "justification": "My account is locked after failed sign-ins.",
        },
    )

    assert response.status_code == 202
    assert response.json()["data"]["status"] == "PENDING"
    assert response.json()["data"]["requester_email"] == email
    assert db.query(AccountUnlockRequest).count() == 1
    assert (
        db.query(AuditLog)
        .filter_by(action="account_unlock_requested", status="SUCCESS")
        .count()
        == 1
    )


def test_account_unlock_request_requires_authentication(client):
    response = client.post(
        "/api/v1/identity/unlock-requests",
        json={
            "email": "employee@example.com",
            "justification": "My account is locked after failed sign-ins.",
        },
    )

    assert response.status_code == 401


def test_only_approvers_can_view_pending_unlock_requests(client):
    employee_headers = token_headers(client, "employee@example.com")
    approver_headers = token_headers(client, "approver@example.com", "Support Engineer")
    submitted = client.post(
        "/api/v1/identity/unlock-requests",
        headers=employee_headers,
        json={
            "email": "employee@example.com",
            "justification": "My account is locked after failed sign-ins.",
        },
    )

    unauthorized = client.get(
        "/api/v1/identity/unlock-requests/pending", headers=employee_headers
    )
    pending = client.get(
        "/api/v1/identity/unlock-requests/pending", headers=approver_headers
    )

    assert submitted.status_code == 202
    assert unauthorized.status_code == 403
    assert len(pending.json()["data"]) == 1


def test_account_unlock_request_rejects_invalid_identity_and_payload(client, db):
    headers = token_headers(client, "employee@example.com")
    auditor_headers = token_headers(client, "auditor@example.com", "Auditor")
    mismatch = client.post(
        "/api/v1/identity/unlock-requests",
        headers=headers,
        json={
            "email": "other@example.com",
            "justification": "My account is locked after failed sign-ins.",
        },
    )
    invalid = client.post(
        "/api/v1/identity/unlock-requests",
        headers=headers,
        json={"email": "not-an-email", "justification": "short"},
    )
    unauthorized = client.post(
        "/api/v1/identity/unlock-requests",
        headers=auditor_headers,
        json={
            "email": "auditor@example.com",
            "justification": "My account is locked after failed sign-ins.",
        },
    )

    assert mismatch.status_code == 403
    assert invalid.status_code == 422
    assert unauthorized.status_code == 403
    assert db.query(AccountUnlockRequest).count() == 0


def test_mfa_reset_succeeds_for_authenticated_user(client, monkeypatch):
    reset = AsyncMock(return_value=2)
    monkeypatch.setattr(graph_service, "reset_mfa_methods", reset)
    headers = token_headers(client, "employee@example.com")

    response = client.post(
        "/api/v1/mfa/reset",
        headers=headers,
        json={"email": "employee@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["methods_removed"] == 2
    reset.assert_awaited_once_with("employee@example.com")


def test_mfa_reset_requires_authentication(client):
    response = client.post(
        "/api/v1/mfa/reset",
        json={"email": "employee@example.com"},
    )

    assert response.status_code == 401


def test_mfa_reset_rejects_role_without_operation_privilege(client):
    headers = token_headers(client, "auditor@example.com", "Auditor")
    response = client.post(
        "/api/v1/mfa/reset",
        headers=headers,
        json={"email": "auditor@example.com"},
    )

    assert response.status_code == 403


def test_mfa_reset_validates_identity_and_surfaces_graph_failure(
    client, db, monkeypatch
):
    headers = token_headers(client, "employee@example.com")
    invalid = client.post(
        "/api/v1/mfa/reset",
        headers=headers,
        json={"email": "not-an-email"},
    )
    mismatch = client.post(
        "/api/v1/mfa/reset",
        headers=headers,
        json={"email": "other@example.com"},
    )
    monkeypatch.setattr(
        graph_service,
        "reset_mfa_methods",
        AsyncMock(
            side_effect=GraphAPIException(
                "Microsoft Graph could not process the authentication reset.",
                status_code=502,
            )
        ),
    )
    failed = client.post(
        "/api/v1/mfa/reset",
        headers=headers,
        json={"email": "employee@example.com"},
    )

    assert invalid.status_code == 422
    assert mismatch.status_code == 403
    assert failed.status_code == 502
    failed_audits = (
        db.query(AuditLog).filter_by(action="mfa_reset", status="FAILED").all()
    )
    assert len(failed_audits) == 2
    assert {audit.details["reason"] for audit in failed_audits} == {
        "identity_verification_failed",
        "GRAPH_API_ERROR",
    }


def test_software_request_creation_and_own_request_visibility(client, db):
    employee_headers = token_headers(client, "employee@example.com")
    other_headers = token_headers(client, "other@example.com")

    created = client.post(
        "/api/v1/software",
        headers=employee_headers,
        json={
            "software_name": " Visual Studio Code ",
            "justification": " Required for platform development work. ",
        },
    )
    own = client.get("/api/v1/software/mine", headers=employee_headers)
    other = client.get("/api/v1/software/mine", headers=other_headers)

    assert created.status_code == 201
    assert created.json()["data"]["status"] == "PENDING"
    assert created.json()["data"]["justification"] == (
        "Required for platform development work."
    )
    assert len(own.json()["data"]) == 1
    assert other.json()["data"] == []
    assert db.query(SoftwareRequest).count() == 1


def test_only_approvers_can_list_pending_and_approve_requests(client, monkeypatch):
    employee_headers = token_headers(client, "employee@example.com")
    approver_headers = token_headers(client, "approver@example.com", "Support Engineer")
    monkeypatch.setattr(
        graph_service, "get_user_phone", AsyncMock(return_value="+15555550123")
    )
    sent_notifications: list[SmsRequest] = []
    monkeypatch.setattr(
        notification_service,
        "send_sms",
        lambda request: sent_notifications.append(request),
    )
    created = client.post(
        "/api/v1/software",
        headers=employee_headers,
        json={
            "software_name": "Draw",
            "justification": "Needed for the design team deliverable.",
        },
    )
    request_id = created.json()["data"]["id"]

    unauthorized = client.post(
        f"/api/v1/software/{request_id}/approve",
        headers=employee_headers,
    )
    pending = client.get("/api/v1/software/pending", headers=approver_headers)
    approved = client.post(
        f"/api/v1/software/{request_id}/approve",
        headers=approver_headers,
        json={"note": "Approved for the design team."},
    )
    duplicate = client.post(
        f"/api/v1/software/{request_id}/approve",
        headers=approver_headers,
    )

    assert unauthorized.status_code == 403
    assert len(pending.json()["data"]) == 1
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "APPROVED"
    assert approved.json()["data"]["decided_by_email"] == "approver@example.com"
    assert len(sent_notifications) == 1
    assert duplicate.status_code == 409


def test_approver_can_reject_and_duplicate_rejection_is_conflict(client, monkeypatch):
    employee_headers = token_headers(client, "employee@example.com")
    approver_headers = token_headers(
        client, "approver@example.com", "Platform Administrator"
    )
    monkeypatch.setattr(
        graph_service, "get_user_phone", AsyncMock(return_value="+15555550123")
    )
    monkeypatch.setattr(notification_service, "send_sms", lambda _request: None)
    created = client.post(
        "/api/v1/software",
        headers=employee_headers,
        json={
            "software_name": "Example Tool",
            "justification": "Required for a project deliverable.",
        },
    )
    request_id = created.json()["data"]["id"]

    rejected = client.post(
        f"/api/v1/software/{request_id}/reject",
        headers=approver_headers,
        json={"note": "An approved alternative is already available."},
    )
    duplicate = client.post(
        f"/api/v1/software/{request_id}/reject",
        headers=approver_headers,
    )

    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "REJECTED"
    assert duplicate.status_code == 409


def test_software_request_validation_and_notification_failure(client, monkeypatch):
    employee_headers = token_headers(client, "employee@example.com")
    approver_headers = token_headers(client, "approver@example.com", "Support Engineer")
    invalid = client.post(
        "/api/v1/software",
        headers=employee_headers,
        json={"software_name": " ", "justification": "short"},
    )
    created = client.post(
        "/api/v1/software",
        headers=employee_headers,
        json={
            "software_name": "Example Tool",
            "justification": "Required for a project deliverable.",
        },
    )
    monkeypatch.setattr(graph_service, "get_user_phone", AsyncMock(return_value=None))

    failure = client.post(
        f"/api/v1/software/{created.json()['data']['id']}/approve",
        headers=approver_headers,
    )

    assert invalid.status_code == 422
    assert failure.status_code == 502
    assert "decision was saved" in failure.json()["error"]["message"]
    assert (
        client.get("/api/v1/software/pending", headers=approver_headers).json()["data"]
        == []
    )
