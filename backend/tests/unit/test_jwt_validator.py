import datetime

import jwt
import pytest

from app.auth.jwt_validator import JWTValidationError, JWTValidator
from app.core.config import settings


@pytest.mark.asyncio
async def test_jwt_validator_mock_mode():
    """Tests JWTValidator resolves and validates mock tokens in local development mode."""
    validator = JWTValidator()

    # Assert validator is initialized in mock mode if client ID is unset
    assert validator.is_mock is True

    # Generate a valid mock token payload
    email = "admin@example.com"
    role = "Platform Administrator"
    now = datetime.datetime.utcnow()
    payload = {
        "preferred_username": email,
        "name": "admin",
        "roles": [role.replace(" ", "")],
        "aud": "MOCK_CLIENT_ID",
        "iss": "https://login.microsoftonline.com/mock-tenant/v2.0",
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(hours=1)).timestamp()),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    # Validate token
    validated_payload = await validator.validate_token(token)
    assert validated_payload["preferred_username"] == email
    assert validated_payload["roles"][0] == "PlatformAdministrator"


@pytest.mark.asyncio
async def test_jwt_validator_expired_token():
    """Tests JWTValidator raises an exception when a token is expired."""
    validator = JWTValidator()

    # Token expired 10 minutes ago
    now = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
    payload = {
        "preferred_username": "user@example.com",
        "roles": ["StandardUser"],
        "aud": "MOCK_CLIENT_ID",
        "iat": int((now - datetime.timedelta(hours=1)).timestamp()),
        "exp": int(now.timestamp()),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    with pytest.raises(JWTValidationError) as excinfo:
        await validator.validate_token(token)

    assert excinfo.value.error_code == "TOKEN_EXPIRED"
    assert "expired" in excinfo.value.message.lower()


@pytest.mark.asyncio
async def test_jwt_validator_invalid_signature():
    """Tests JWTValidator rejects tokens signed with incorrect secret keys."""
    validator = JWTValidator()

    payload = {
        "preferred_username": "user@example.com",
        "roles": ["StandardUser"],
        "aud": "MOCK_CLIENT_ID",
        "exp": int(
            (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).timestamp()
        ),
    }

    # Sign with a bad secret key
    token = jwt.encode(payload, "BAD_SECRET_KEY", algorithm="HS256")

    with pytest.raises(JWTValidationError) as excinfo:
        await validator.validate_token(token)

    assert excinfo.value.status_code == 401
    assert "invalid mock" in excinfo.value.message.lower()
