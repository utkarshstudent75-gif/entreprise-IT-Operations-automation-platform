from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.orm import Session

from app.auth.providers.base import BaseAuthenticationProvider
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import user_repository


class LocalAuthenticationProvider(BaseAuthenticationProvider):
    """Local database and JWT authentication provider."""

    def verify_token(self, db: Session, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id_str = payload.get("sub")
            if not user_id_str:
                return None
            user_id = int(user_id_str)
            return user_repository.get_by_id(db, user_id)
        except (jwt.PyJWTError, ValueError):
            return None

    def create_access_token(
        self, user_id: int, expires_delta: timedelta | None = None
    ) -> str:
        to_encode = {"sub": str(user_id)}
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
