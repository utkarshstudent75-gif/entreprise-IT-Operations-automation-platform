from datetime import UTC, datetime, timedelta
import pytest

from app.api.v1.audit import get_audit_log, get_audit_logs
from app.core.exceptions import BaseAppException
from app.models.audit_log import AuditLog
from app.models.user import User


def call_get_audit_logs(db, **kwargs):
    """Helper to call get_audit_logs directly with correct defaults,
    bypassing Query objects.
    """
    defaults = {
        "user_id": None,
        "action": None,
        "status": None,
        "start_date": None,
        "end_date": None,
        "skip": 0,
        "limit": 100,
    }
    defaults.update(kwargs)
    return get_audit_logs(db=db, **defaults)


def test_get_audit_logs_empty(db):
    logs_res = call_get_audit_logs(db=db)
    assert logs_res.data == []


def test_get_audit_log_by_id(db):
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

    res = get_audit_log(audit_id=log.id, db=db)
    data = res.data
    assert data.id == log.id
    assert data.action == "user_creation"
    assert data.status == "SUCCESS"
    assert data.user_id == user.id
    assert data.ip_address == "127.0.0.1"
    assert data.user_agent == "TestUA"
    assert data.request_id == "req-111"
    assert data.details == {"username": "testuser"}


def test_get_audit_log_not_found(db):
    with pytest.raises(BaseAppException) as excinfo:
        get_audit_log(audit_id=9999, db=db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Audit log not found."


def test_get_audit_logs_filtering(db):
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

    # Filter by user_id
    logs_res = call_get_audit_logs(db=db, user_id=user1.id)
    logs = logs_res.data
    assert len(logs) == 1
    assert logs[0].action == "user_creation"

    # Filter by action
    logs_res = call_get_audit_logs(db=db, action="password_reset")
    logs = logs_res.data
    assert len(logs) == 1
    assert logs[0].action == "password_reset"

    # Filter by status
    logs_res = call_get_audit_logs(db=db, status="FAILED")
    logs = logs_res.data
    assert len(logs) == 1
    assert logs[0].status == "FAILED"

    # Filter by date range
    start_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    logs_res = call_get_audit_logs(db=db, start_date=start_date)
    logs = logs_res.data
    assert len(logs) == 1
    assert logs[0].action == "password_reset"
