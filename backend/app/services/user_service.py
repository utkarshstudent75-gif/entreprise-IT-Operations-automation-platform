from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import status

from app.core.exceptions import DuplicateUserException
from app.core.logging_config import logger
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserResponse
from app.services.audit_service import audit_service


class UserService:
    """
    Handles user creation business logic and validation.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_user(self, db: Session, request: UserCreate) -> UserResponse:
        if user_repository.get_by_username(db, request.username):
            logger.warning("Username %s already exists", request.username)
            audit_service.record_event(
                action="user_creation",
                status="FAILED",
                details={"username": request.username, "email": request.email, "reason": "Username already exists"},
            )
            raise DuplicateUserException("Username already exists.")

        if user_repository.get_by_email(db, request.email):
            logger.warning("Email %s already exists", request.email)
            audit_service.record_event(
                action="user_creation",
                status="FAILED",
                details={"username": request.username, "email": request.email, "reason": "Email already exists"},
            )
            raise DuplicateUserException("Email already exists.")

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
            audit_service.record_event(
                action="user_creation",
                status="FAILED",
                details={"username": request.username, "email": request.email, "reason": "Unique constraint violation"},
            )
            raise DuplicateUserException("Username or email already exists.")

        except Exception as e:
            logger.error(
                "Unexpected error while creating user %s: %s",
                request.username,
                str(e),
                exc_info=True,
            )
            audit_service.record_event(
                action="user_creation",
                status="FAILED",
                details={"username": request.username, "email": request.email, "reason": str(e)},
            )
            raise

        logger.info("Created user %s with id %s", user.username, user.id)
        audit_service.record_event(
            action="user_creation",
            status="SUCCESS",
            user_id=user.id,
            details={"username": user.username, "email": user.email},
        )

        return UserResponse.model_validate(user)

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)


user_service = UserService()

