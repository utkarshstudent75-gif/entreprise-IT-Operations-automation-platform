from datetime import UTC, datetime, timedelta

from app.core.context import request_id, request_ip, request_user_agent
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.audit_service import audit_service


def test_record_event_success(db):
    # Set context variables
    token_ip = request_ip.set("127.0.0.1")
    token_ua = request_user_agent.set("TestAgent")
    token_rid = request_id.set("req-123")

    try:
        # Create a user to reference
        user = User(
            username="audituser", email="audit@example.com", hashed_password="pwd"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

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
        db_log = db.query(AuditLog).filter_by(id=log.id).first()
        assert db_log is not None
        assert db_log.action == "user_creation"
    finally:
        request_ip.reset(token_ip)
        request_user_agent.reset(token_ua)
        request_id.reset(token_rid)


def test_record_event_resiliency(db, monkeypatch):
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


def test_list_logs_and_get_by_id(db):
    # Pre-populate logs
    log1 = AuditLog(
        action="test_action_1",
        status="SUCCESS",
        timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=10),
    )
    log2 = AuditLog(
        action="test_action_2",
        status="FAILED",
        timestamp=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(log1)
    db.add(log2)
    db.commit()

    # Test get by ID
    fetched = audit_service.get_log_by_id(db, log1.id)
    assert fetched is not None
    assert fetched.action == "test_action_1"

    # Test list_logs
    logs = audit_service.list_logs(db)
    assert len(logs) >= 2
    assert logs[0].action == "test_action_2"  # ordered by timestamp desc

    # Test list_logs filtering
    logs_filtered = audit_service.list_logs(db, action="test_action_1")
    assert len(logs_filtered) == 1
    assert logs_filtered[0].action == "test_action_1"
