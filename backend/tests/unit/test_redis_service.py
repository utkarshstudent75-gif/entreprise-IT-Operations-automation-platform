from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import (
    ExpiredOTPException,
    InvalidOTPException,
    OTPAlreadyUsedException,
)
from app.services.redis_service import RedisService, redis_service


def test_redis_service_generate_key():
    email = "user@example.com"
    key = redis_service.generate_key(email)
    assert key == f"otp:{email}"
    assert redis_service._get_key(email) == f"otp:{email}"


@pytest.mark.asyncio
async def test_store_otp():
    service = RedisService()
    mock_client = AsyncMock()

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        await service.store_otp("user@example.com", "123456", 300)

        mock_client.hset.assert_called_once()
        mock_client.expire.assert_called_once_with("otp:user@example.com", 300)
        mock_client.set.assert_called_once_with(
            "otp:meta:user@example.com", "1", ex=300 * 24
        )


@pytest.mark.asyncio
async def test_get_otp():
    service = RedisService()
    mock_client = AsyncMock()
    mock_client.hgetall.return_value = {"otp_hash": "hash123", "attempts": "0"}

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        result = await service.get_otp("user@example.com")
        assert result == {"otp_hash": "hash123", "attempts": "0"}
        mock_client.hgetall.assert_called_once_with("otp:user@example.com")


@pytest.mark.asyncio
async def test_get_otp_empty():
    service = RedisService()
    mock_client = AsyncMock()
    mock_client.hgetall.return_value = {}

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        result = await service.get_otp("user@example.com")
        assert result is None


@pytest.mark.asyncio
async def test_increment_and_clear_attempts():
    service = RedisService()
    mock_client = AsyncMock()
    mock_client.hincrby.return_value = 1

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        attempts = await service.increment_attempts("user@example.com")
        assert attempts == 1
        mock_client.hincrby.assert_called_once_with(
            "otp:user@example.com", "attempts", 1
        )

        await service.clear_attempts("user@example.com")
        mock_client.hset.assert_called_once_with(
            "otp:user@example.com", "attempts", "0"
        )


@pytest.mark.asyncio
async def test_delete_otp():
    service = RedisService()
    mock_client = AsyncMock()

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        await service.delete_otp("user@example.com")
        assert mock_client.delete.call_count == 2


@pytest.mark.asyncio
async def test_verify_otp_success_non_consuming():
    service = RedisService()
    email = "user@example.com"
    otp = "123456"
    otp_hash = service._hash_otp(otp)

    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {"otp_hash": otp_hash, "attempts": "0"}

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        result = await service.verify_otp(email, otp, consume=False)
        assert result is True


@pytest.mark.asyncio
async def test_verify_otp_success_consuming():
    service = RedisService()
    email = "user@example.com"
    otp = "123456"
    otp_hash = service._hash_otp(otp)

    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {"otp_hash": otp_hash, "attempts": "0"}

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        result = await service.verify_otp(
            email, otp, consume=True, expires_in_seconds=300
        )
        assert result is True
        # Verify active OTP deleted and marked in used_key
        mock_client.delete.assert_any_call(f"otp:{email}")
        mock_client.set.assert_called_once_with(f"otp:used:{email}", otp_hash, ex=300)


@pytest.mark.asyncio
async def test_verify_otp_already_used():
    service = RedisService()
    email = "user@example.com"
    otp = "123456"
    otp_hash = service._hash_otp(otp)

    mock_client = AsyncMock()
    mock_client.get.return_value = otp_hash

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        with pytest.raises(OTPAlreadyUsedException):
            await service.verify_otp(email, otp)


@pytest.mark.asyncio
async def test_verify_otp_expired():
    service = RedisService()
    email = "user@example.com"

    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {}
    mock_client.exists.return_value = True

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        with pytest.raises(ExpiredOTPException):
            await service.verify_otp(email, "123456")


@pytest.mark.asyncio
async def test_verify_otp_missing():
    service = RedisService()
    email = "user@example.com"

    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {}
    mock_client.exists.return_value = False

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        with pytest.raises(InvalidOTPException):
            await service.verify_otp(email, "123456")


@pytest.mark.asyncio
async def test_verify_otp_mismatch_increments_attempts():
    service = RedisService()
    email = "user@example.com"
    correct_hash = service._hash_otp("123456")

    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {"otp_hash": correct_hash, "attempts": "1"}
    mock_client.hincrby.return_value = 2

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        with pytest.raises(InvalidOTPException):
            await service.verify_otp(email, "000000", max_attempts=3)
        mock_client.hincrby.assert_called_once_with(f"otp:{email}", "attempts", 1)


@pytest.mark.asyncio
async def test_verify_otp_max_attempts_lockout():
    service = RedisService()
    email = "user@example.com"
    correct_hash = service._hash_otp("123456")

    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.hgetall.return_value = {"otp_hash": correct_hash, "attempts": "3"}

    with patch("app.services.redis_service.get_redis", return_value=mock_client):
        with pytest.raises(InvalidOTPException):
            await service.verify_otp(email, "123456", max_attempts=3)
        mock_client.delete.assert_any_call(f"otp:{email}")
