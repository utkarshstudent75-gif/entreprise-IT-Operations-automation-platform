from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.database.base import Base
from app.models.audit_log import AuditLog
from app.api.v1.audit import get_audit_logs, get_audit_log


# Setup sqlite database for router testing
engine = create_engine("sqlite:///:memory:", echo=False, future=True)
Base.metadata.create_all(engine)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def sqlite_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_db(sqlite_db):
    # Clean table before each test
    sqlite_db.query(AuditLog).delete()
    sqlite_db.commit()


def call_get_audit_logs(db, **kwargs):
    """Helper to call get_audit_logs directly with correct defaults, bypassing Query objects."""
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


def test_get_audit_logs_empty(sqlite_db):
    logs = call_get_audit_logs(db=sqlite_db)
    assert logs == []


def test_get_audit_log_by_id(sqlite_db):
    log = AuditLog(
        action="user_creation",
        status="SUCCESS",
        user_id=1,
        ip_address="127.0.0.1",
        user_agent="TestUA",
        request_id="req-111",
        details={"username": "testuser"},
    )
    sqlite_db.add(log)
    sqlite_db.commit()
    sqlite_db.refresh(log)

    data = get_audit_log(audit_id=log.id, db=sqlite_db)
    assert data.id == log.id
    assert data.action == "user_creation"
    assert data.status == "SUCCESS"
    assert data.user_id == 1
    assert data.ip_address == "127.0.0.1"
    assert data.user_agent == "TestUA"
    assert data.request_id == "req-111"
    assert data.details == {"username": "testuser"}


def test_get_audit_log_not_found(sqlite_db):
    with pytest.raises(HTTPException) as excinfo:
        get_audit_log(audit_id=9999, db=sqlite_db)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Audit log not found."


def test_get_audit_logs_filtering(sqlite_db):
    log1 = AuditLog(
        action="user_creation",
        status="SUCCESS",
        user_id=1,
        timestamp=datetime.utcnow() - timedelta(days=2),
    )
    log2 = AuditLog(
        action="password_reset",
        status="FAILED",
        user_id=2,
        timestamp=datetime.utcnow(),
    )
    sqlite_db.add(log1)
    sqlite_db.add(log2)
    sqlite_db.commit()

    # Filter by user_id
    logs = call_get_audit_logs(db=sqlite_db, user_id=1)
    assert len(logs) == 1
    assert logs[0].action == "user_creation"

    # Filter by action
    logs = call_get_audit_logs(db=sqlite_db, action="password_reset")
    assert len(logs) == 1
    assert logs[0].action == "password_reset"

    # Filter by status
    logs = call_get_audit_logs(db=sqlite_db, status="FAILED")
    assert len(logs) == 1
    assert logs[0].status == "FAILED"

    # Filter by date range
    start_date = datetime.utcnow() - timedelta(days=1)
    logs = call_get_audit_logs(db=sqlite_db, start_date=start_date)
    assert len(logs) == 1
    assert logs[0].action == "password_reset"
