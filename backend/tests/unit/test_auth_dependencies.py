from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.auth.dependencies import get_current_user
from app.auth.jwt_validator import jwt_validator


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entra_role", "expected_role"),
    [
        ("Platform.Admin", "Platform Administrator"),
        ("Platform.IT", "Support Engineer"),
    ],
)
async def test_current_user_maps_existing_entra_app_roles(
    monkeypatch, entra_role, expected_role
):
    claims = {
        "preferred_username": "operator@example.com",
        "roles": [entra_role],
    }
    monkeypatch.setattr(
        jwt_validator, "validate_token", AsyncMock(return_value=claims)
    )
    request = Request({"type": "http", "headers": [], "method": "GET", "path": "/"})
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-token"
    )

    user = await get_current_user(request, credentials)

    assert user["role"] == expected_role
