from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.core.context import request_id, request_ip, request_user_agent
from app.models.audit_log import AuditLog
from app.services.audit_service import audit_service


def test_record_event_success(monkeypatch):
    """
    Test that recording an audit log entry works correctly under normal conditions.

    This test mocks:
      - SessionLocal: to return a dummy DB session mock.
      - audit_repository.create_entry: to return a dummy AuditLog.

    It verifies that:
      - The event is created with the exact arguments passed.
      - The DB session is committed/closed.
      - The returned value is the created AuditLog.
    """
    mock_session = MagicMock()
    mock_session_local = MagicMock(return_value=mock_session)
    monkeypatch.setattr("app.services.audit_service.SessionLocal", mock_session_local)

    dummy_log = AuditLog(id=123, action="test_action", status="SUCCESS")
    mock_create_entry = MagicMock(return_value=dummy_log)
    monkeypatch.setattr(
        "app.services.audit_service.audit_repository.create_entry", mock_create_entry
    )

    details_payload = {"key": "val"}
    timestamp_val = datetime.now(UTC).replace(tzinfo=None)

    log = audit_service.record_event(
        action="test_action",
        status="SUCCESS",
        user_id=1,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_id_val="req-abc",
        details=details_payload,
        timestamp=timestamp_val,
    )

    # Verify that SessionLocal was called to get a database session
    mock_session_local.assert_called_once()

    # Verify that the repository's create_entry was called with correct parameters
    mock_create_entry.assert_called_once_with(
        db=mock_session,
        action="test_action",
        status="SUCCESS",
        user_id=1,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        request_id="req-abc",
        details=details_payload,
        timestamp=timestamp_val,
    )

    # Verify session close was called
    mock_session.close.assert_called_once()
    assert log == dummy_log


def test_record_event_resolves_context(monkeypatch):
    """
    Test that record_event resolves ip_address, user_agent, and request_id from
    the request context variables when they are not explicitly provided.

    This test verifies that context propagation works correctly.
    """
    mock_session = MagicMock()
    monkeypatch.setattr(
        "app.services.audit_service.SessionLocal", MagicMock(return_value=mock_session)
    )

    mock_create_entry = MagicMock(return_value=AuditLog())
    monkeypatch.setattr(
        "app.services.audit_service.audit_repository.create_entry", mock_create_entry
    )

    # Set context variables using contextvars tokens
    ip_token = request_ip.set("10.0.0.5")
    ua_token = request_user_agent.set("ContextAgent")
    rid_token = request_id.set("ctx-req-id")

    try:
        audit_service.record_event(action="context_action", status="SUCCESS")

        # Verify resolved values were passed to repository
        mock_create_entry.assert_called_once()
        kwargs = mock_create_entry.call_args[1]
        assert kwargs["ip_address"] == "10.0.0.5"
        assert kwargs["user_agent"] == "ContextAgent"
        assert kwargs["request_id"] == "ctx-req-id"
    finally:
        # Reset context variables to keep tests clean
        request_ip.reset(ip_token)
        request_user_agent.reset(ua_token)
        request_id.reset(rid_token)


def test_record_event_resilience_on_exception(monkeypatch):
    """
    Test the resiliency of record_event.

    If the database session creation or repository insert throws an exception,
    the exception must be logged and swallowed, returning None instead of propagating
    the exception to the caller. This ensures audit failures do not break the main application flow.
    """
    mock_session = MagicMock()
    monkeypatch.setattr(
        "app.services.audit_service.SessionLocal", MagicMock(return_value=mock_session)
    )

    # Repository throws an database operational/connection error
    def raise_db_error(*args, **kwargs):
        raise Exception("Database connection failure")

    monkeypatch.setattr(
        "app.services.audit_service.audit_repository.create_entry", raise_db_error
    )

    # Record the event. It should not raise an error.
    log = audit_service.record_event(action="resilient_action", status="SUCCESS")

    assert log is None
    # Verify the session is still closed in the finally block
    mock_session.close.assert_called_once()


def test_get_log_by_id(monkeypatch):
    """
    Test that get_log_by_id delegates call correctly to the repository with the DB session.
    """
    mock_db = MagicMock()
    dummy_log = AuditLog(id=456)
    mock_get_by_id = MagicMock(return_value=dummy_log)
    monkeypatch.setattr(
        "app.services.audit_service.audit_repository.get_by_id", mock_get_by_id
    )

    result = audit_service.get_log_by_id(mock_db, 456)

    mock_get_by_id.assert_called_once_with(mock_db, 456)
    assert result == dummy_log


def test_list_logs(monkeypatch):
    """
    Test that list_logs delegates calls and filters correctly to the repository get_all method.
    """
    mock_db = MagicMock()
    mock_logs = [AuditLog(id=1), AuditLog(id=2)]
    mock_get_all = MagicMock(return_value=mock_logs)
    monkeypatch.setattr(
        "app.services.audit_service.audit_repository.get_all", mock_get_all
    )

    start_t = datetime(2026, 1, 1)
    end_t = datetime(2026, 1, 2)

    result = audit_service.list_logs(
        db=mock_db,
        user_id=10,
        action="login",
        status="SUCCESS",
        start_date=start_t,
        end_date=end_t,
        skip=5,
        limit=20,
    )

    mock_get_all.assert_called_once_with(
        db=mock_db,
        user_id=10,
        action="login",
        status="SUCCESS",
        start_date=start_t,
        end_date=end_t,
        skip=5,
        limit=20,
    )
    assert result == mock_logs
