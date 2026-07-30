import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from app.models.audit_log import AuditLog


@pytest.fixture
def mock_standard_user():
    return {
        "email": "test-standard@example.com",
        "name": "test-standard",
        "role": "Standard User",
        "claims": {
            "preferred_username": "test-standard@example.com",
            "name": "test-standard",
            "roles": ["StandardUser"],
            "iat": 1700000000,
            "exp": 1700005000,
        },
    }


@pytest.fixture
def mock_admin_user():
    return {
        "email": "test-admin@example.com",
        "name": "test-admin",
        "role": "Platform Administrator",
        "claims": {
            "preferred_username": "test-admin@example.com",
            "name": "test-admin",
            "roles": ["PlatformAdministrator"],
            "iat": 1700000000,
            "exp": 1700005000,
        },
    }


def test_dashboard_summary_standard_user(client, db, mock_standard_user):
    # Set dependency override
    app.dependency_overrides[get_current_user] = lambda: mock_standard_user

    # Add mock audit logs
    log1 = AuditLog(
        action="password_reset",
        status="SUCCESS",
        details={"email": "test-standard@example.com"},
        ip_address="127.0.0.1",
    )
    log2 = AuditLog(
        action="password_reset",
        status="FAILED",
        details={"email": "test-standard@example.com"},
        ip_address="127.0.0.1",
    )
    log3 = AuditLog(
        action="password_reset",
        status="SUCCESS",
        details={"email": "other-user@example.com"},
        ip_address="127.0.0.1",
    )
    db.add_all([log1, log2, log3])
    db.commit()

    try:
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]
        assert data["total_requests"] == 2
        assert data["successful_resets"] == 1
        assert data["failed_resets"] == 1
        assert data["pending_approvals"] == 0
    finally:
        app.dependency_overrides.clear()


def test_dashboard_summary_admin_user(client, db, mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    log1 = AuditLog(
        action="password_reset",
        status="SUCCESS",
        details={"email": "test-standard@example.com"},
        ip_address="127.0.0.1",
    )
    log2 = AuditLog(
        action="password_reset",
        status="SUCCESS",
        details={"email": "other-user@example.com"},
        ip_address="127.0.0.1",
    )
    db.add_all([log1, log2])
    db.commit()

    try:
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_requests"] == 2
        assert data["successful_resets"] == 2
        assert data["pending_approvals"] == 2
    finally:
        app.dependency_overrides.clear()


def test_dashboard_recent_activity_filtering(client, db, mock_standard_user):
    app.dependency_overrides[get_current_user] = lambda: mock_standard_user

    log1 = AuditLog(
        action="password_reset",
        status="SUCCESS",
        details={"email": "test-standard@example.com"},
        ip_address="127.0.0.1",
    )
    log2 = AuditLog(
        action="password_reset",
        status="SUCCESS",
        details={"email": "other-user@example.com"},
        ip_address="127.0.0.1",
    )
    db.add_all([log1, log2])
    db.commit()

    try:
        response = client.get("/api/v1/dashboard/recent-activity")
        assert response.status_code == 200
        data = response.json()["data"]
        # Standard user should only see their log
        assert len(data) == 1
        assert data[0]["details"]["email"] == "test-standard@example.com"
    finally:
        app.dependency_overrides.clear()


def test_dashboard_notifications_role_separation(
    client, mock_standard_user, mock_admin_user
):
    # 1. Standard user notifications
    app.dependency_overrides[get_current_user] = lambda: mock_standard_user
    try:
        response = client.get("/api/v1/dashboard/notifications")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert "SSO Login Success" in data[0]["title"]
    finally:
        app.dependency_overrides.clear()

    # 2. Admin user notifications
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    try:
        response = client.get("/api/v1/dashboard/notifications")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        titles = [n["title"] for n in data]
        assert "MFA Security Review" in titles
    finally:
        app.dependency_overrides.clear()
