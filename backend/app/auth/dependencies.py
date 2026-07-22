from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.service import auth_service
from app.core.context import user_id
from app.core.exceptions import AuthenticationException, BaseAppException
from app.database.dependencies import get_db
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security_scheme)
    ],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if not credentials:
        raise AuthenticationException("Missing authorization credentials.")

    token = credentials.credentials
    user = auth_service.verify_token(db, token)
    if not user:
        raise AuthenticationException("Could not validate credentials.")

    # Set the request context user ID for audit logging
    user_id.set(user.id)
    return user


def require_roles(*allowed_roles: str):
    """Enforce that the authenticated user possesses one of the allowed roles."""

    def role_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_roles = [r.strip() for r in current_user.roles.split(",") if r.strip()]
        if not any(role in user_roles for role in allowed_roles):
            raise BaseAppException(
                "Operation not permitted with your current role.",
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="INSUFFICIENT_PERMISSIONS",
            )
        return current_user

    return role_dependency
