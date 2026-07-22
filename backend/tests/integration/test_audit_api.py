from datetime import UTC, datetime, timedelta

import pytest

from app.auth.dependencies import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.fixture(autouse=True)
def override_auth(client):
    mock_user = User(
        id=999,
        username="admin_test",
        email="admin@example.com",
        roles="Admin",
    )
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_get_audit_logs_empty(client):
    """Verify that retrieval of audit logs returns an empty list when no entries exist."""
    response = client.get("/api/v1/audit-logs")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"] == []


def test_get_audit_log_by_id(client, db):
    """Verify that a single audit log entry is correctly retrieved by its integer ID."""
    user = User(username="testuser", email="test@example.com", hashed_password="pwd")
    db.add(user)
    db.commit()
    db.refresh(user)

    log = AuditLog(
        action="user_creation",
        status="SUCCESS",
        user_id=user.id,
        ip_address="127.0.0.1",
        user_agent="TestUA",
        request_id="req-111",
        details={"username": "testuser"},
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    response = client.get(f"/api/v1/audit-logs/{log.id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True

    data = json_data["data"]
    assert data["id"] == log.id
    assert data["action"] == "user_creation"
    assert data["status"] == "SUCCESS"
    assert data["user_id"] == user.id
    assert data["ip_address"] == "127.0.0.1"
    assert data["user_agent"] == "TestUA"
    assert data["request_id"] == "req-111"
    assert data["details"] == {"username": "testuser"}


def test_get_audit_log_not_found(client):
    """Verify retrieving a non-existent audit log returns a 404 and AUDIT_LOG_NOT_FOUND error code."""
    response = client.get("/api/v1/audit-logs/9999")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "AUDIT_LOG_NOT_FOUND"
    assert json_data["error"]["message"] == "Audit log not found."


def test_get_audit_logs_filtering(client, db):
    """Verify that GET /api/v1/audit-logs supports filtering by user_id, action, status, and start_date."""
    user1 = User(username="user1", email="user1@example.com", hashed_password="pwd")
    user2 = User(username="user2", email="user2@example.com", hashed_password="pwd")
    db.add(user1)
    db.add(user2)
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    log1 = AuditLog(
        action="user_creation",
        status="SUCCESS",
        user_id=user1.id,
        timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2),
    )
    log2 = AuditLog(
        action="password_reset",
        status="FAILED",
        user_id=user2.id,
        timestamp=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(log1)
    db.add(log2)
    db.commit()

    # 1. Filter by user_id
    res = client.get(f"/api/v1/audit-logs?user_id={user1.id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["action"] == "user_creation"

    # 2. Filter by action
    res = client.get("/api/v1/audit-logs?action=password_reset")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["action"] == "password_reset"

    # 3. Filter by status
    res = client.get("/api/v1/audit-logs?status=FAILED")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["status"] == "FAILED"

    # 4. Filter by date range (start_date)
    start_date = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    res = client.get(f"/api/v1/audit-logs?start_date={start_date}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["action"] == "password_reset"
