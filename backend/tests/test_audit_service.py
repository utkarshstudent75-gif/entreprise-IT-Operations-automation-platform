from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.context import request_id, request_ip, request_user_agent
from app.database.base import Base
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.audit_service import audit_service


@pytest.fixture
def sqlite_db():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = SessionLocal()
    try:
        # Prevent close during testing so we can verify records
        db.close = lambda: None
        yield db
    finally:
        # Actually close the database connection
        db.bind.dispose()


@pytest.fixture(autouse=True)
def patch_session_local(sqlite_db, monkeypatch):
    monkeypatch.setattr("app.services.audit_service.SessionLocal", lambda: sqlite_db)
    yield


def test_record_event_success(sqlite_db):
    # Set context variables
    token_ip = request_ip.set("127.0.0.1")
    token_ua = request_user_agent.set("TestAgent")
    token_rid = request_id.set("req-123")

    try:
        # Create a user to reference
        user = User(
            username="audituser", email="audit@example.com", hashed_password="pwd"
        )
        sqlite_db.add(user)
        sqlite_db.commit()
        sqlite_db.refresh(user)

        # Record event
        log = audit_service.record_event(
            action="user_creation",
            status="SUCCESS",
            user_id=user.id,
            details={"foo": "bar"},
        )

        assert log is not None
        assert log.id is not None
        assert log.action == "user_creation"
        assert log.status == "SUCCESS"
        assert log.user_id == user.id
        assert log.ip_address == "127.0.0.1"
        assert log.user_agent == "TestAgent"
        assert log.request_id == "req-123"
        assert log.details == {"foo": "bar"}

        # Fetch from DB and verify
        db_log = sqlite_db.query(AuditLog).filter_by(id=log.id).first()
        assert db_log is not None
        assert db_log.action == "user_creation"
    finally:
        request_ip.reset(token_ip)
        request_user_agent.reset(token_ua)
        request_id.reset(token_rid)


def test_record_event_resiliency(sqlite_db, monkeypatch):
    # Test that exception in repository/db doesn't break the application, it
    # returns None
    def mock_create_entry(*args, **kwargs):
        raise Exception("DB Error simulated")

    monkeypatch.setattr(
        "app.services.audit_service.audit_repository.create_entry", mock_create_entry
    )

    log = audit_service.record_event(
        action="user_creation",
        status="SUCCESS",
    )
    # Failure should be swallowed and return None
    assert log is None


def test_list_logs_and_get_by_id(sqlite_db):
    # Pre-populate logs
    log1 = AuditLog(
        action="test_action_1",
        status="SUCCESS",
        timestamp=datetime.utcnow() - timedelta(minutes=10),
    )
    log2 = AuditLog(
        action="test_action_2",
        status="FAILED",
        timestamp=datetime.utcnow(),
    )
    sqlite_db.add(log1)
    sqlite_db.add(log2)
    sqlite_db.commit()

    # Test get by ID
    fetched = audit_service.get_log_by_id(sqlite_db, log1.id)
    assert fetched is not None
    assert fetched.action == "test_action_1"

    # Test list_logs
    logs = audit_service.list_logs(sqlite_db)
    assert len(logs) >= 2
    assert logs[0].action == "test_action_2"  # ordered by timestamp desc

    # Test list_logs filtering
    logs_filtered = audit_service.list_logs(sqlite_db, action="test_action_1")
    assert len(logs_filtered) == 1
    assert logs_filtered[0].action == "test_action_1"
