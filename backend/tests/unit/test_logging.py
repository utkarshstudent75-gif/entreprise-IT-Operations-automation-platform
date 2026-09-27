import json
import logging
import sys
import uuid
from unittest.mock import MagicMock

import pytest

from app.core.context import (
    action,
    get_or_create_request_id,
    logging_context,
    request_id,
    user_id,
)
from app.core.logging_config import StructuredJSONFormatter, setup_logging


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
    assert "user_id" not in data


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
        assert "user_id" not in data
        assert "extra" not in data
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


def test_request_id_rejects_unstructured_user_values():
    request_id_value = get_or_create_request_id("private@example.com")
    parsed_request_id = uuid.UUID(request_id_value)

    assert str(parsed_request_id) == request_id_value
    assert "private@example.com" not in request_id_value


def test_request_id_preserves_uuid_correlation():
    request_id_value = "12345678-1234-5678-1234-567812345678"

    assert get_or_create_request_id(request_id_value) == request_id_value


def test_setup_logging_disables_uvicorn_access_records():
    access_logger = logging.getLogger("uvicorn.access")
    original_disabled = access_logger.disabled
    try:
        setup_logging()
        assert access_logger.disabled
    finally:
        access_logger.disabled = original_disabled


def test_logging_failures_never_raise():
    formatter = StructuredJSONFormatter()
    # Passing None triggers an exception in format() but it must handle it gracefully
    formatted = formatter.format(None)
    data = json.loads(formatted)
    assert "timestamp" in data
    assert data["message"] == "Structured logging formatter failure."


def test_json_formatter_does_not_include_exception_messages_or_extra_fields():
    try:
        raise ValueError("password=private OTP=735194")
    except ValueError:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test_path.py",
            lineno=30,
            msg="Authentication failed",
            args=(),
            exc_info=sys.exc_info(),
        )
    record.password = "private"
    record.otp = "735194"

    data = json.loads(StructuredJSONFormatter().format(record))

    assert data["exception_type"] == "ValueError"
    assert "private" not in json.dumps(data)
    assert "735194" not in json.dumps(data)
    assert "password" not in data
    assert "otp" not in data


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
        import asyncio

        await asyncio.sleep(0)
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
