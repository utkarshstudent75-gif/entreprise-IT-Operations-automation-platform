from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import logging_context, user_id
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
        with logging_context(act="user_creation"):
            if user_repository.get_by_username(db, request.username):
                logger.warning(
                    "User creation rejected because username already exists."
                )
                audit_service.record_event(
                    action="user_creation",
                    status="FAILED",
                    details={
                        "username": request.username,
                        "email": request.email,
                        "reason": "Username already exists",
                    },
                )
                raise DuplicateUserException("Username already exists.")

            if user_repository.get_by_email(db, request.email):
                logger.warning("User creation rejected because email already exists.")
                audit_service.record_event(
                    action="user_creation",
                    status="FAILED",
                    details={
                        "username": request.username,
                        "email": request.email,
                        "reason": "Email already exists",
                    },
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
                logger.warning("User creation rejected by a unique constraint.")
                audit_service.record_event(
                    action="user_creation",
                    status="FAILED",
                    details={
                        "username": request.username,
                        "email": request.email,
                        "reason": "Unique constraint violation",
                    },
                )
                raise DuplicateUserException("Username or email already exists.")

            except Exception as e:
                logger.error("Unexpected user creation error (%s).", type(e).__name__)
                audit_service.record_event(
                    action="user_creation",
                    status="FAILED",
                    details={
                        "username": request.username,
                        "email": request.email,
                        "reason": str(e),
                    },
                )
                raise

            user_id.set(user.id)

            logger.info("User created successfully.")
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
