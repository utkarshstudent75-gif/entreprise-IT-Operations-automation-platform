import pytest

from app.core.exceptions import (
    ExpiredOTPException,
    InvalidOTPException,
)
from app.models.user import User
from app.services.password_reset_service import (
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)
from app.services.redis_service import redis_service


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


async def test_request_password_reset_returns_success_for_unknown_email(monkeypatch):
    """
    Test that request_password_reset returns None even if
    the requested email is not found in the database.
    """
    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: None,
    )

    result = await password_reset_service.request_password_reset(
        DummyDB(), "missing@example.com"
    )

    assert result is None


async def test_request_password_reset_creates_request_and_sends_otp(monkeypatch):
    """
    Test that request_password_reset successfully generates an OTP and stores it in Redis.
    """
    user = DummyUser(id=1, email="test@example.com")
    stored = {}

    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: user,
    )

    async def mock_store_otp(email, otp, expires_in_seconds):
        stored.update(
            {"email": email, "otp": otp, "expires_in_seconds": expires_in_seconds}
        )

    monkeypatch.setattr(redis_service, "store_otp", mock_store_otp)
    monkeypatch.setattr(
        "app.services.password_reset_service.notification_service.send_otp",
        lambda email, otp: None,
    )

    result = await password_reset_service.request_password_reset(DummyDB(), user.email)

    assert result is None
    assert stored["email"] == user.email
    assert len(stored["otp"]) == 6
    assert stored["expires_in_seconds"] == settings_otp_expiry_seconds()


def settings_otp_expiry_seconds():
    from app.core.config import settings

    return settings.OTP_EXPIRY_MINUTES * 60


async def test_verify_otp_raises_when_no_user(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetInvalidRequest exception (400)
    if the provided email is not registered.
    """
    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: None,
    )

    db = DummyDB()
    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.verify_otp(db, "missing@example.com", "000000")


async def test_verify_otp_raises_when_no_request(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetInvalidRequest exception (400)
    if there is no active record in Redis.
    """
    user = DummyUser(id=1, email="test@example.com")
    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: user,
    )

    async def mock_verify_otp(email, otp, consume, max_attempts, expires_in_seconds):
        raise InvalidOTPException("Invalid email or OTP.")

    monkeypatch.setattr(redis_service, "verify_otp", mock_verify_otp)

    db = DummyDB()
    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.verify_otp(db, user.email, "000000")


async def test_verify_otp_raises_when_expired(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetExpiredError exception (410)
    if the reset request has expired.
    """
    user = DummyUser(id=1, email="test@example.com")
    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: user,
    )

    async def mock_verify_otp(email, otp, consume, max_attempts, expires_in_seconds):
        raise ExpiredOTPException("OTP has expired.")

    monkeypatch.setattr(redis_service, "verify_otp", mock_verify_otp)

    db = DummyDB()
    with pytest.raises(PasswordResetExpiredError):
        await password_reset_service.verify_otp(db, user.email, "123456")


async def test_verify_otp_raises_when_mismatch(monkeypatch):
    """
    Test that verifying an OTP raises a PasswordResetInvalidRequest exception (400)
    if the OTP mismatches.
    """
    user = DummyUser(id=1, email="test@example.com")
    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: user,
    )

    async def mock_verify_otp(email, otp, consume, max_attempts, expires_in_seconds):
        raise InvalidOTPException("Invalid email or OTP.")

    monkeypatch.setattr(redis_service, "verify_otp", mock_verify_otp)

    db = DummyDB()
    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.verify_otp(db, user.email, "000000")


async def test_verify_otp_returns_true_for_matching_otp(monkeypatch):
    """
    Test that verify_otp returns True when the OTP matches.
    """
    user = DummyUser(id=1, email="test@example.com")
    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: user,
    )

    async def mock_verify_otp(email, otp, consume, max_attempts, expires_in_seconds):
        return True

    monkeypatch.setattr(redis_service, "verify_otp", mock_verify_otp)

    assert (
        await password_reset_service.verify_otp(DummyDB(), user.email, "123456") is True
    )


async def test_reset_password_updates_password(monkeypatch):
    """
    Test that reset_password successfully updates the user's password hash and consumes OTP.
    """
    user = DummyUser(id=1, email="test@example.com")
    user.hashed_password = "oldhash"

    monkeypatch.setattr(
        "app.repositories.user_repository.user_repository.get_by_email",
        lambda db, email: user,
    )

    async def mock_verify_otp(email, otp, consume, max_attempts, expires_in_seconds):
        assert consume is True
        return True

    monkeypatch.setattr(redis_service, "verify_otp", mock_verify_otp)

    assert (
        await password_reset_service.reset_password(
            DummyDB(), user.email, "123456", "NewPassword@123"
        )
        is True
    )
    assert user.hashed_password != "oldhash"
