from datetime import UTC, datetime, timedelta

import pytest

from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User
from app.repositories.password_reset_repository import password_reset_repository
from app.repositories.user_repository import user_repository
from app.services.password_reset_service import (
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)


class DummyDB:
    """
    A lightweight mock of SQLAlchemy's DB session class used
    to isolate tests from real database connection calls.
    """

    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def add(self, _):
        pass

    def commit(self):
        pass

    def refresh(self, _):
        pass


class DummyUser(User):
    """
    A mock User model inheriting from the SQL Alchemy User model
    to bypass strict ORM constructors during unit testing.
    """

    def __init__(self, id: int, email: str):
        self.id = id
        self.email = email
        self.hashed_password = ""


class DummyResetRequest(PasswordResetRequest):
    """
    A mock PasswordResetRequest model used to represent a stored reset request record.
    """

    pass


def test_request_password_reset_returns_success_for_unknown_email(monkeypatch):
    """
    Test that request_password_reset returns True (indicating success) even if
    the requested email is not found in the database.

    This acts as a security measure to prevent user enumeration attacks:
    an attacker shouldn't be able to guess registered emails by looking at response status.
    """
    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: None)

    result = password_reset_service.request_password_reset(
        DummyDB(), "missing@example.com"
    )

    assert result is True


def test_request_password_reset_creates_request_and_sends_otp(monkeypatch):
    """
    Test that request_password_reset successfully creates a new reset request,
    generates a 6-digit OTP with an future expiry time, and triggers the notification service.

    Verified outcomes:
      - Returns True.
      - Generated OTP contains 6 characters.
      - Expiry is set to a future time.
    """
    user = DummyUser(id=1, email="test@example.com")
    created = {}

    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: user)
    monkeypatch.setattr(
        password_reset_repository,
        "create_reset_request",
        lambda db, user_id, otp, expires_at: (
            created.update({"user_id": user_id, "otp": otp, "expires_at": expires_at})
            or DummyResetRequest()
        ),
    )
    monkeypatch.setattr(
        "app.services.password_reset_service.notification_service.send_otp",
        lambda email, otp: None,
    )

    result = password_reset_service.request_password_reset(DummyDB(), user.email)

    assert result is True
    assert created["user_id"] == user.id
    assert len(created["otp"]) == 6
    assert created["expires_at"] > datetime.now(UTC).replace(tzinfo=None)


def test_verify_otp_raises_when_no_user(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetInvalidRequest exception (400)
    if the provided email is not registered.
    """
    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: None)

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(DummyDB(), "missing@example.com", "000000")


def test_verify_otp_raises_when_no_request(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetInvalidRequest exception (400)
    if there is no record of a password reset request for that user.
    """
    user = DummyUser(id=1, email="test@example.com")
    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: user)
    monkeypatch.setattr(
        password_reset_repository, "get_latest_request", lambda db, user_id: None
    )

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(DummyDB(), user.email, "000000")


def test_verify_otp_raises_when_expired(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetExpiredError exception (410)
    if the reset request has expired.
    """
    user = DummyUser(id=1, email="test@example.com")
    reset_request = PasswordResetRequest(
        user_id=1,
        otp="123456",
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: user)
    monkeypatch.setattr(
        password_reset_repository,
        "get_latest_request",
        lambda db, user_id: reset_request,
    )

    with pytest.raises(PasswordResetExpiredError):
        password_reset_service.verify_otp(DummyDB(), user.email, "123456")


def test_verify_otp_raises_when_mismatch(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetInvalidRequest exception (400)
    if the provided OTP code does not match the generated code stored in the database.
    """
    user = DummyUser(id=1, email="test@example.com")
    reset_request = PasswordResetRequest(
        user_id=1,
        otp="123456",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=5),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: user)
    monkeypatch.setattr(
        password_reset_repository,
        "get_latest_request",
        lambda db, user_id: reset_request,
    )

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(DummyDB(), user.email, "000000")


def test_verify_otp_returns_true_for_matching_otp(monkeypatch):
    """
    Test that verify_otp returns True when the user exists, a valid/unexpired
    request is active, and the submitted OTP code matches the stored one.
    """
    user = DummyUser(id=1, email="test@example.com")
    reset_request = PasswordResetRequest(
        user_id=1,
        otp="123456",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=5),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: user)
    monkeypatch.setattr(
        password_reset_repository,
        "get_latest_request",
        lambda db, user_id: reset_request,
    )

    assert password_reset_service.verify_otp(DummyDB(), user.email, "123456") is True


def test_reset_password_marks_request_used_and_updates_password(monkeypatch):
    """
    Test that reset_password successfully updates the user's password hash and
    marks the password reset request as used (is_used=True) when all validation constraints pass.
    """
    user = DummyUser(id=1, email="test@example.com")
    user.hashed_password = "oldhash"
    reset_request = PasswordResetRequest(
        user_id=1,
        otp="123456",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=5),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: user)
    monkeypatch.setattr(
        password_reset_repository,
        "get_latest_request",
        lambda db, user_id: reset_request,
    )

    assert (
        password_reset_service.reset_password(
            DummyDB(), user.email, "123456", "NewPassword@123"
        )
        is True
    )
    assert reset_request.is_used is True
    assert user.hashed_password != "oldhash"
