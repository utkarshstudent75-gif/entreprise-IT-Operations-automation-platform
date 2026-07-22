from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BaseAppException, AuthenticationException
from app.database.dependencies import get_db
from app.repositories.user_repository import user_repository
from app.schemas.response import StandardResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.services.user_service import user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[UserResponse],
)
async def create_user(request: UserCreate, db: Annotated[Session, Depends(get_db)]):
    user = user_service.create_user(db, request)
    return StandardResponse(data=user)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[TokenResponse],
)
async def login_user(
    request: UserLogin,
    db: Annotated[Session, Depends(get_db)],
):
    if settings.AUTH_PROVIDER != "local":
        raise BaseAppException(
            "Local login is disabled when Entra ID is active.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="LOCAL_LOGIN_DISABLED",
        )

    # Search for user by email first, then username
    user = user_repository.get_by_email(db, request.username_or_email)
    if not user:
        user = user_repository.get_by_username(db, request.username_or_email)

    if not user or not user.hashed_password:
        raise AuthenticationException("Invalid username or password.")

    if not user_service.pwd_context.verify(request.password, user.hashed_password):
        raise AuthenticationException("Invalid username or password.")

    from app.auth.service import auth_service
    from app.auth.providers.local import LocalAuthenticationProvider

    if not isinstance(auth_service, LocalAuthenticationProvider):
        raise BaseAppException(
            "Incorrect auth provider active.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PROVIDER_MISMATCH",
        )

    access_token = auth_service.create_access_token(user_id=user.id)

    from app.services.audit_service import audit_service
    from app.core.context import user_id as ctx_user_id

    ctx_user_id.set(user.id)
    audit_service.record_event(
        action="user_login",
        status="SUCCESS",
        user_id=user.id,
        details={"username": user.username, "email": user.email},
    )

    return StandardResponse(
        data=TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )
    )

