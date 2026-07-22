import asyncio
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.core.redis import get_redis
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.notification_service import notification_service
from app.services.password_reset_service import (
    PasswordResetAlreadyUsedError,
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)
from app.services.redis_service import redis_service


async def test_password_reset_flow_works_end_to_end(db, monkeypatch, caplog):
    user = User(
        username="ajay",
        email="ajaykumar@example.com",
        hashed_password="oldhash",  # NOSONAR
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    sent_notifications = []
    monkeypatch.setattr(
        notification_service,
        "send_otp",
        lambda email, otp: sent_notifications.append((email, otp)),
    )

    caplog.set_level("INFO")
    result = await password_reset_service.request_password_reset(db, user.email)

    assert result is None
    assert sent_notifications, "OTP notification should be sent"
    assert sent_notifications[0][0] == user.email
    assert len(sent_notifications[0][1]) == 6

    # Verify stored in Redis
    otp_data = await redis_service.get_otp(user.email)
    assert otp_data is not None
    assert "otp_hash" in otp_data
    assert int(otp_data["attempts"]) == 0
    assert "Password reset request created for user id" in caplog.text

    # Verify TTL exists in Redis
    client = await get_redis()
    ttl = await client.ttl(f"otp:{user.email}")
    assert ttl > 0
    meta_ttl = await client.ttl(f"otp:meta:{user.email}")
    assert meta_ttl > 0

    otp_code = sent_notifications[0][1]
    assert await password_reset_service.verify_otp(db, user.email, otp_code) is True

    assert (
        await password_reset_service.reset_password(
            db, user.email, otp_code, "NewPassword@123"
        )
        is True
    )

    db.refresh(user)
    assert user.hashed_password != "oldhash"
    assert "Password reset completed for user id" in caplog.text

    # OTP should be gone/consumed
    otp_data_after = await redis_service.get_otp(user.email)
    assert otp_data_after is None

    # Verify no stale OTPs remain
    assert await client.exists(f"otp:{user.email}") == 0
    assert await client.exists(f"otp:meta:{user.email}") == 0

    # Verify audit logs written
    forgot_log = (
        db.query(AuditLog).filter_by(action="forgot_password", user_id=user.id).first()
    )
    assert forgot_log is not None
    assert forgot_log.status == "SUCCESS"
    assert forgot_log.details.get("email") == user.email

    reset_log = (
        db.query(AuditLog).filter_by(action="password_reset", user_id=user.id).first()
    )
    assert reset_log is not None
    assert reset_log.status == "SUCCESS"
    assert reset_log.details.get("email") == user.email

    # Should raise Already Used on reuse
    with pytest.raises(PasswordResetAlreadyUsedError):
        await password_reset_service.reset_password(
            db, user.email, otp_code, "AnotherPass@123"
        )


async def test_expired_otp_is_rejected(db):
    user = User(
        username="ajay2",
        email="expired@example.com",
        hashed_password="oldhash2",  # NOSONAR
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Simulate expired OTP: meta key exists, but active key is gone
    client = await get_redis()
    await client.set(f"otp:meta:{user.email}", "1", ex=60)
    await client.delete(f"otp:{user.email}")

    with pytest.raises(PasswordResetExpiredError):
        await password_reset_service.reset_password(
            db, user.email, "000999", "NewPassword@123"
        )


async def test_unknown_email_request_returns_success(db):
    assert (
        await password_reset_service.request_password_reset(db, "missing@example.com")
        is None
    )


async def test_verify_otp_rejects_invalid_code(db):
    user = User(
        username="ajay3",
        email="mismatch@example.com",
        hashed_password="oldhash3",  # NOSONAR
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    await redis_service.store_otp(user.email, "123456", 300)

    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.verify_otp(db, user.email, "000000")


async def test_otp_expiration_real_redis(db, monkeypatch):
    user = User(
        username="expire_test",
        email="expire@example.com",
        hashed_password="oldhash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Monkeypatch settings to expire in 1 second
    monkeypatch.setattr(settings, "OTP_EXPIRY_MINUTES", 1 / 60)

    # Mock send_otp to prevent real SMS API calls causing test delay
    sent_notifications = []
    monkeypatch.setattr(
        notification_service,
        "send_otp",
        lambda email, otp: sent_notifications.append((email, otp)),
    )

    # Request password reset
    await password_reset_service.request_password_reset(db, user.email)

    # Verify keys exist in Redis immediately
    client = await get_redis()
    assert await client.exists(f"otp:{user.email}") == 1
    assert await client.exists(f"otp:meta:{user.email}") == 1

    # Wait for expiration (1.2 seconds to be safe)
    await asyncio.sleep(1.2)

    # Verify active key is gone (expired)
    assert await client.exists(f"otp:{user.email}") == 0
    # Note: meta key lasts longer (ex = ex * 24), so it should still exist
    assert await client.exists(f"otp:meta:{user.email}") == 1

    # Verification fails after expiration
    with pytest.raises(PasswordResetExpiredError):
        await password_reset_service.reset_password(
            db, user.email, "123456", "NewPassword@123"
        )


async def test_retry_counter_real_redis(db, monkeypatch):
    user = User(
        username="retry_test",
        email="retry@example.com",
        hashed_password="oldhash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    sent_notifications = []
    monkeypatch.setattr(
        notification_service,
        "send_otp",
        lambda email, otp: sent_notifications.append((email, otp)),
    )

    await password_reset_service.request_password_reset(db, user.email)

    # Verify retry count initialized to 0
    otp_data = await redis_service.get_otp(user.email)
    assert int(otp_data["attempts"]) == 0

    # Wrong OTP increments retry count in Redis
    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.reset_password(
            db, user.email, "wrongcode", "NewPassword@123"
        )

    otp_data = await redis_service.get_otp(user.email)
    assert int(otp_data["attempts"]) == 1

    # Second wrong attempt increments to 2
    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.reset_password(
            db, user.email, "wrongcode2", "NewPassword@123"
        )
    otp_data = await redis_service.get_otp(user.email)
    assert int(otp_data["attempts"]) == 2

    # Third wrong attempt (exceeds limit) deletes the key and fails
    with pytest.raises(PasswordResetInvalidRequest):
        await password_reset_service.reset_password(
            db, user.email, "wrongcode3", "NewPassword@123"
        )

    # OTP removed after exceeding limit
    otp_data_after = await redis_service.get_otp(user.email)
    assert otp_data_after is None

    # Verify no stale keys remain in Redis
    client = await get_redis()
    assert await client.exists(f"otp:{user.email}") == 0
    assert await client.exists(f"otp:meta:{user.email}") == 0


async def test_wrong_redis_config():
    from app.core.redis import RedisManager

    # Instantiate manager with bad configuration
    bad_manager = RedisManager()
    # Mock settings to have wrong host/port
    with patch("app.core.redis.settings") as mock_settings:
        mock_settings.REDIS_URL = None
        mock_settings.REDIS_HOST = "invalid_host_name"
        mock_settings.REDIS_PORT = 9999
        mock_settings.REDIS_DB = 0
        mock_settings.REDIS_PASSWORD = None

        bad_manager.init_redis()
        assert await bad_manager.ping() is False


def test_redis_unavailable_during_verification(db, monkeypatch):
    user = User(
        username="unavail_test",
        email="test@example.com",
        hashed_password="oldhash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Mock get_redis to raise an error
    async def mock_get_redis_raise():
        raise Exception("Redis connection lost")

    monkeypatch.setattr("app.services.redis_service.get_redis", mock_get_redis_raise)
    monkeypatch.setattr("app.core.redis.get_redis", mock_get_redis_raise)

    # Initialize a local TestClient with raise_server_exceptions=False to test HTTP status codes
    from fastapi.testclient import TestClient

    from app.main import app

    local_client = TestClient(app, raise_server_exceptions=False)

    # 1. verify-otp catches general exception and returns 400 (structured INVALID_OTP error)
    response_verify = local_client.post(
        "/api/v1/password/verify-otp",
        json={"email": "test@example.com", "otp": "123456"},
    )
    assert response_verify.status_code == 400
    assert response_verify.json()["success"] is False
    assert response_verify.json()["error"]["code"] == "INVALID_OTP"

    # 2. forgot-password propagates the exception and returns 500 (structured INTERNAL_SERVER_ERROR)
    response_forgot = local_client.post(
        "/api/v1/password/forgot-password",
        json={"email": "test@example.com"},
    )
    assert response_forgot.status_code == 500
    assert response_forgot.json()["success"] is False
    assert response_forgot.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
