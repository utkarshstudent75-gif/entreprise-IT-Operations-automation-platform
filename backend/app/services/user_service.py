from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.logging_config import logger
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserResponse


class UserService:
    """
    Handles user creation business logic and validation.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_user(self, db: Session, request: UserCreate) -> UserResponse:
        if user_repository.get_by_username(db, request.username):
            logger.warning("Username %s already exists", request.username)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            )

        if user_repository.get_by_email(db, request.email):
            logger.warning("Email %s already exists", request.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            )

        hashed_password = self._hash_password(request.password)

        try:
            user = user_repository.create_user(
                db=db,
                username=request.username,
                email=request.email,
                hashed_password=hashed_password,
            )
        except IntegrityError:
            logger.warning(
                "Unique constraint violation while creating user %s / %s",
                request.username,
                request.email,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists.",
            )

        logger.info("Created user %s with id %s", user.username, user.id)

        return UserResponse.model_validate(user)

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)


user_service = UserService()
