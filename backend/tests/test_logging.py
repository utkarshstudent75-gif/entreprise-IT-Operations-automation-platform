import json
import logging
import pytest
from unittest.mock import MagicMock

from app.core.context import request_id, user_id, action, logging_context
from app.core.logging_config import StructuredJSONFormatter


def test_json_formatter_standard():
    formatter = StructuredJSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path.py",
        lineno=10,
        msg="Hello %s!",
        args=("World",),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["module"] == "test_path"
    assert data["message"] == "Hello World!"
    assert data["request_id"] is None
    assert data["action"] is None
    assert data["user_id"] is None


def test_json_formatter_with_context():
    req_token = request_id.set("req-123")
    user_token = user_id.set("user-456")
    action_token = action.set("test_action")

    try:
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="test_path.py",
            lineno=20,
            msg="Warning message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "WARNING"
        assert data["request_id"] == "req-123"
        assert data["action"] == "test_action"
        assert data["user_id"] == "user-456"
    finally:
        request_id.reset(req_token)
        user_id.reset(user_token)
        action.reset(action_token)


def test_logging_context_manager():
    assert action.get() is None
    assert user_id.get() is None

    with logging_context(act="my_action", u_id=999):
        assert action.get() == "my_action"
        assert user_id.get() == 999

        with logging_context(act="other_action", u_id=111):
            assert action.get() == "other_action"
            assert user_id.get() == 111

        assert action.get() == "my_action"
        assert user_id.get() == 999

    assert action.get() is None
    assert user_id.get() is None


def test_logging_failures_never_raise():
    formatter = StructuredJSONFormatter()
    # Passing None triggers an exception in format() but it must handle it gracefully
    formatted = formatter.format(None)
    data = json.loads(formatted)
    assert "timestamp" in data
    assert "Logging formatter failure" in data["message"]


@pytest.mark.anyio
async def test_middleware_request_id_and_logs():
    from app.main import add_audit_context_middleware
    
    # Mock FastAPI request
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"

    # Mock call_next function that verifies request_id context is set during call
    async def call_next(req):
        assert request_id.get() is not None
        assert len(request_id.get()) == 36
        response = MagicMock()
        response.headers = {}
        return response

    response = await add_audit_context_middleware(request, call_next)
    
    # After middleware executes, it should set x-request-id on response
    assert "x-request-id" in response.headers
    # After request completes, context variables should be cleaned up
    assert request_id.get() is None
    assert user_id.get() is None
    assert action.get() is None
