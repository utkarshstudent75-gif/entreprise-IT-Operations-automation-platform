from datetime import datetime, timedelta
import secrets

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.repositories.password_reset_repository import password_reset_repository
from app.repositories.user_repository import user_repository
from app.services.notification_service import notification_service


class PasswordResetError(Exception):
    """Base exception for password reset business rules."""


class PasswordResetInvalidRequest(PasswordResetError):
    """Raised when the submitted OTP or email cannot be validated."""


class PasswordResetExpiredError(PasswordResetError):
    """Raised when the OTP has expired."""


class PasswordResetAlreadyUsedError(PasswordResetError):
    """Raised when the OTP has already been consumed."""


class PasswordResetService:
    """Encapsulates password reset business logic separate from repository code."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def request_password_reset(self, db: Session, email: str) -> bool:
        """Create a reset request and send the OTP.

        If the user does not exist, return success anyway to prevent
        user enumeration. This avoids leaking whether an email is registered.
        """
        user = user_repository.get_by_email(db, email)

        if user is None:
            logger.info(
                "Password reset requested for unknown email %s; returning success to avoid enumeration.",
                email,
            )
            return True

        otp = self._generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        password_reset_repository.create_reset_request(
            db=db,
            user_id=user.id,
            otp=otp,
            expires_at=expires_at,
        )

        # TODO: replace this console-level notification with a real email/SMS provider.
        notification_service.send_otp(email, otp)

        logger.info("Password reset request created for user id %s", user.id)
        return True

    def verify_otp(self, db: Session, email: str, otp: str) -> bool:
        """Verify a submitted OTP without consuming it.

        This method validates existence, usage state, expiry, and OTP match.
        Business rules stay in the service layer; the repository only fetches data.
        """
        user = user_repository.get_by_email(db, email)
        if user is None:
            logger.warning("Password reset verify failed for unknown email %s", email)
            raise PasswordResetInvalidRequest("Invalid email or OTP.")

        reset_request = password_reset_repository.get_latest_valid_request(db, user.id)
        if reset_request is None:
            logger.warning("No password reset request found for user id %s", user.id)
            raise PasswordResetInvalidRequest("Invalid email or OTP.")

        if reset_request.is_used:
            logger.warning("Password reset request already used for user id %s", user.id)
            raise PasswordResetAlreadyUsedError("OTP has already been used.")

        if datetime.utcnow() > reset_request.expires_at:
            logger.warning("Password reset OTP expired for user id %s", user.id)
            raise PasswordResetExpiredError("OTP has expired.")

        if reset_request.otp != otp:
            logger.warning("Password reset OTP mismatch for user id %s", user.id)
            raise PasswordResetInvalidRequest("Invalid email or OTP.")

        logger.info("Password reset OTP verified for user id %s", user.id)
        return True

    def reset_password(self, db: Session, email: str, otp: str, new_password: str) -> bool:
        """Reset a user's password in a single transactional operation."""
        user = user_repository.get_by_email(db, email)
        if user is None:
            logger.warning("Password reset failed for unknown email %s", email)
            raise PasswordResetInvalidRequest("Invalid email or OTP.")

        reset_request = password_reset_repository.get_latest_request(db, user.id)
        if reset_request is None:
            logger.warning("No password reset request found for reset on user id %s", user.id)
            raise PasswordResetInvalidRequest("Invalid email or OTP.")

        if reset_request.is_used:
            logger.warning("Attempted password reset with used OTP for user id %s", user.id)
            raise PasswordResetAlreadyUsedError("OTP has already been used.")

        if datetime.utcnow() > reset_request.expires_at:
            logger.warning("Attempted password reset with expired OTP for user id %s", user.id)
            raise PasswordResetExpiredError("OTP has expired.")

        if reset_request.otp != otp:
            logger.warning("Password reset OTP mismatch for user id %s", user.id)
            raise PasswordResetInvalidRequest("Invalid email or OTP.")

        hashed_password = self._hash_password(new_password)

        user.hashed_password = hashed_password
        reset_request.is_used = True
        db.add(user)
        db.add(reset_request)
        db.commit()
        db.refresh(user)
        db.refresh(reset_request)

        logger.info("Password reset completed for user id %s", user.id)
        return True

    def _generate_otp(self) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(6))

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)


password_reset_service = PasswordResetService()
