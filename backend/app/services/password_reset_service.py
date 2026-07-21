import secrets
from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import logging_context, user_id
from app.core.exceptions import (
    ExpiredOTPException,
    InvalidOTPException,
    OTPAlreadyUsedException,
    PasswordResetException,
)
from app.core.logging_config import logger
from app.repositories.password_reset_repository import password_reset_repository
from app.repositories.user_repository import user_repository
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service

INVALID_EMAIL_OR_OTP = "Invalid email or OTP."
OTP_EXPIRED = "OTP has expired."
OTP_ALREADY_USED_MSG = "OTP has already been used."


class PasswordResetError(PasswordResetException):
    """Base exception for password reset business rules."""

    def __init__(self, message: str = "Password reset error."):
        super().__init__(message)


class PasswordResetInvalidRequest(PasswordResetError, InvalidOTPException):
    """Raised when the submitted OTP or email cannot be validated."""

    def __init__(self, message: str = INVALID_EMAIL_OR_OTP):
        super().__init__(message)
        self.error_code = "INVALID_OTP"
        self.status_code = 400


class PasswordResetExpiredError(PasswordResetError, ExpiredOTPException):
    """Raised when the OTP has expired."""

    def __init__(self, message: str = OTP_EXPIRED):
        super().__init__(message)
        self.error_code = "EXPIRED_OTP"
        self.status_code = 410


class PasswordResetAlreadyUsedError(PasswordResetError, OTPAlreadyUsedException):
    """Raised when the OTP has already been consumed."""

    def __init__(self, message: str = OTP_ALREADY_USED_MSG):
        super().__init__(message)
        self.error_code = "OTP_ALREADY_USED"
        self.status_code = 400


class PasswordResetService:
    """Encapsulates password reset business logic separate from repository code."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def request_password_reset(self, db: Session, email: str) -> None:
        """Create a reset request and send the OTP.

        If the user does not exist, complete the call successfully anyway to prevent
        user enumeration. This avoids leaking whether an email is registered.
        """
        with logging_context(act="password_reset_requested"):
            user = user_repository.get_by_email(db, email)
            if user:
                user_id.set(user.id)

            if user is None:
                logger.info(
                    "Password reset requested for unknown email %s; "
                    "returning success to avoid enumeration.",
                    email,
                )
                audit_service.record_event(
                    action="forgot_password",
                    status="FAILED",
                    details={"email": email, "reason": "Unknown email"},
                )
                return

            otp = self._generate_otp()
            expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
                minutes=settings.OTP_EXPIRY_MINUTES
            )

            try:
                password_reset_repository.create_reset_request(
                    db=db,
                    user_id=user.id,
                    otp=otp,
                    expires_at=expires_at,
                )
            except Exception as e:
                logger.error("Failed to create password reset request: %s", str(e))
                audit_service.record_event(
                    action="forgot_password",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": str(e)},
                )
                raise

            # Send the OTP using notification_service
            notification_service.send_otp(email, otp)

            logger.info("Password reset request created for user id %s", user.id)
            audit_service.record_event(
                action="forgot_password",
                status="SUCCESS",
                user_id=user.id,
                details={"email": email},
            )

    def verify_otp(self, db: Session, email: str, otp: str) -> bool:
        """Verify a submitted OTP without consuming it.

        This method validates existence, usage state, expiry, and OTP match.
        Business rules stay in the service layer; the repository only fetches data.
        """
        with logging_context(act="otp_verification"):
            user = user_repository.get_by_email(db, email)
            if user:
                user_id.set(user.id)

            if user is None:
                logger.warning(
                    "Password reset verify failed for unknown email %s", email
                )
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    details={
                        "email": email,
                        "reason": INVALID_EMAIL_OR_OTP.rstrip("."),
                    },
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            reset_request = password_reset_repository.get_latest_request(db, user.id)
            if reset_request is None:
                logger.warning(
                    "No password reset request found for user id %s", user.id
                )
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "No valid request found"},
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            if reset_request.is_used:
                logger.warning(
                    "Password reset request already used for user id %s", user.id
                )
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "OTP already used"},
                )
                raise PasswordResetAlreadyUsedError(OTP_ALREADY_USED_MSG)

            if datetime.now(UTC).replace(tzinfo=None) > reset_request.expires_at:
                logger.warning("Password reset OTP expired for user id %s", user.id)
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "OTP expired"},
                )
                raise PasswordResetExpiredError(OTP_EXPIRED)

            if reset_request.otp != otp:
                logger.warning("Password reset OTP mismatch for user id %s", user.id)
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "OTP mismatch"},
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            logger.info("Password reset OTP verified for user id %s", user.id)
            audit_service.record_event(
                action="otp_verification",
                status="SUCCESS",
                user_id=user.id,
                details={"email": email},
            )
            return True

    def reset_password(
        self, db: Session, email: str, otp: str, new_password: str
    ) -> bool:
        """Reset a user's password in a single transactional operation."""
        with logging_context(act="password_reset_completed"):
            user = user_repository.get_by_email(db, email)
            if user:
                user_id.set(user.id)

            if user is None:
                logger.warning("Password reset failed for unknown email %s", email)
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    details={
                        "email": email,
                        "reason": INVALID_EMAIL_OR_OTP.rstrip("."),
                    },
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            reset_request = password_reset_repository.get_latest_request(db, user.id)
            if reset_request is None:
                logger.warning(
                    "No password reset request found for reset on user id %s", user.id
                )
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "No request found"},
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            if reset_request.is_used:
                logger.warning(
                    "Attempted password reset with used OTP for user id %s", user.id
                )
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "OTP already used"},
                )
                raise PasswordResetAlreadyUsedError(OTP_ALREADY_USED_MSG)

            if datetime.now(UTC).replace(tzinfo=None) > reset_request.expires_at:
                logger.warning(
                    "Attempted password reset with expired OTP for user id %s", user.id
                )
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "OTP expired"},
                )
                raise PasswordResetExpiredError(OTP_EXPIRED)

            if reset_request.otp != otp:
                logger.warning("Password reset OTP mismatch for user id %s", user.id)
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": "OTP mismatch"},
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            hashed_password = self._hash_password(new_password)

            user.hashed_password = hashed_password
            reset_request.is_used = True

            try:
                db.add(user)
                db.add(reset_request)
                db.commit()
                db.refresh(user)
                db.refresh(reset_request)
            except Exception as e:
                logger.error(
                    "Failed database transaction for reset_password: %s", str(e)
                )
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    user_id=user.id,
                    details={"email": email, "reason": f"Database error: {str(e)}"},
                )
                raise

            logger.info("Password reset completed for user id %s", user.id)
            audit_service.record_event(
                action="password_reset",
                status="SUCCESS",
                user_id=user.id,
                details={"email": email},
            )
            return True

    def _generate_otp(self) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(6))

    def _hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)


password_reset_service = PasswordResetService()
