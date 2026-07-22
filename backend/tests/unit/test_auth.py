import pytest
import jwt
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, patch
from fastapi import status

from app.core.config import settings
from app.core.exceptions import BaseAppException
from app.models.user import User
from app.auth.providers.local import LocalAuthenticationProvider
from app.auth.providers.entra import EntraAuthenticationProvider
from app.auth.jwt_validator import EntraJWTValidator


def test_local_provider_token_flow(db):
    provider = LocalAuthenticationProvider()
    
    # Create test user
    user = User(username="test_local", email="local@example.com", hashed_password="pwd", roles="HelpDesk")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    token = provider.create_access_token(user_id=user.id)
    assert token is not None
    
    # Verify token
    verified_user = provider.verify_token(db, token)
    assert verified_user is not None
    assert verified_user.id == user.id
    assert verified_user.email == "local@example.com"


def test_local_provider_invalid_token(db):
    provider = LocalAuthenticationProvider()
    
    # Verify mock/garbage token
    assert provider.verify_token(db, "garbage_token") is None
    
    # Expired token
    expired_token = provider.create_access_token(user_id=999, expires_delta=timedelta(seconds=-10))
    assert provider.verify_token(db, expired_token) is None


@patch("app.auth.jwt_validator.EntraJWTValidator.validate_token")
def test_entra_provider_user_mapping_new(mock_validate, db):
    mock_validate.return_value = {
        "oid": "entra-oid-123",
        "email": "entra_new@example.com",
        "name": "New Entra User",
        "tid": "tenant-456",
    }
    
    provider = EntraAuthenticationProvider()
    
    # Ensure user doesn't exist initially
    user_in_db = db.query(User).filter(User.email == "entra_new@example.com").one_or_none()
    assert user_in_db is None
    
    # Verify and map token
    user = provider.verify_token(db, "valid_entra_token")
    assert user is not None
    assert user.entra_oid == "entra-oid-123"
    assert user.email == "entra_new@example.com"
    assert user.display_name == "New Entra User"
    assert user.entra_tenant_id == "tenant-456"
    assert user.roles == "HelpDesk"
    assert user.last_login is not None


@patch("app.auth.jwt_validator.EntraJWTValidator.validate_token")
def test_entra_provider_user_mapping_existing_link(mock_validate, db):
    # Pre-create local user with same email
    existing_user = User(
        username="existing_local",
        email="entra_existing@example.com",
        hashed_password="pwd",
        roles="Admin"
    )
    db.add(existing_user)
    db.commit()
    db.refresh(existing_user)
    
    mock_validate.return_value = {
        "oid": "entra-oid-789",
        "email": "entra_existing@example.com",
        "name": "Updated Display Name",
        "tid": "tenant-456",
    }
    
    provider = EntraAuthenticationProvider()
    
    # Verify and map token (should link instead of creating)
    user = provider.verify_token(db, "valid_entra_token")
    assert user is not None
    assert user.id == existing_user.id
    assert user.entra_oid == "entra-oid-789"
    assert user.display_name == "Updated Display Name"
    assert user.roles == "Admin"  # Keep role


def test_entra_jwt_validator_failures():
    validator = EntraJWTValidator()
    
    # 1. Invalid token format
    with pytest.raises(BaseAppException) as exc:
        validator.validate_token("not-a-jwt")
    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_TOKEN"

    # 2. Missing tenant ID claim
    token_missing_tid = jwt.encode({"sub": "123"}, "secret", algorithm="HS256")
    with pytest.raises(BaseAppException) as exc:
        validator.validate_token(token_missing_tid)
    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_TOKEN"

    # 3. Tenant mismatch (Tenant lock check)
    settings.ENTRA_TENANT_ID = "tenant-xyz"
    token_wrong_tenant = jwt.encode({"sub": "123", "tid": "tenant-wrong"}, "secret", algorithm="HS256")
    with pytest.raises(BaseAppException) as exc:
        validator.validate_token(token_wrong_tenant)
    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_ISSUER"
    settings.ENTRA_TENANT_ID = None
