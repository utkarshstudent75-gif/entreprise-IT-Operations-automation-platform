import datetime
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt_validator import jwt_validator
from app.core.config import settings
from app.database.dependencies import get_db
from app.schemas.response import StandardResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


class MockTokenRequest(BaseModel):
    email: str
    role: str


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[UserResponse],
)
async def create_user(request: UserCreate, db: Annotated[Session, Depends(get_db)]):
    user = user_service.create_user(db, request)
    return StandardResponse(data=user)


@router.post(
    "/mock-token",
    status_code=status.HTTP_200_OK,
)
async def generate_mock_token(request: MockTokenRequest):
    """
    Developer SSO Token Generator.
    Only enabled when ENTRA_CLIENT_ID configuration is empty/mock mode.
    """
    if not jwt_validator.is_mock:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock SSO authentication is disabled in production environments."
        )

    # Validate role is valid
    valid_roles = ["Standard User", "Platform Administrator", "Support Engineer", "Auditor"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid security role. Must be one of: {valid_roles}"
        )

    now = datetime.datetime.utcnow()
    payload = {
        "preferred_username": request.email,
        "name": request.email.split("@")[0],
        "roles": [request.role.replace(" ", "")], # standard Entra ID formats them without spaces
        "aud": settings.ENTRA_CLIENT_ID or "MOCK_CLIENT_ID",
        "iss": f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID or 'mock-tenant'}/v2.0",
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(hours=1)).timestamp())
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return StandardResponse(data={"token": token})


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Returns the currently logged-in user profile, mapped from Entra ID claims.
    """
    return StandardResponse(data={
        "email": current_user["email"],
        "name": current_user["name"],
        "role": current_user["role"]
    })

