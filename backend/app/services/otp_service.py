import secrets
from datetime import UTC, datetime

from fastapi import status

from app.core.config import settings
from app.core.context import logging_context
from app.core.exceptions import (
    BaseAppException,
    ExpiredOTPException,
    InvalidOTPException,
)
from app.core.logging_config import logger
from app.database.otp_repository import otp_repository


class OTPService:
    """
    Handles OTP generation and verification.
    """

    def generate_otp(self, email: str) -> str:
        """
        Generate a secure OTP and store it.
        """

        logger.info("Generating OTP for %s", email)

        otp = "".join(str(secrets.randbelow(10)) for _ in range(settings.OTP_LENGTH))

        otp_repository.save_otp(
            email=email,
            otp=otp,
            expiry_minutes=settings.OTP_EXPIRY_MINUTES,
        )

        logger.info("OTP generated successfully for %s", email)

        return otp

    def verify_otp(self, email: str, otp: str) -> bool:
        """
        Verify the OTP submitted by the user.
        """
        with logging_context(act="otp_verification"):
            record = otp_repository.get_otp(email)

            if record is None:
                logger.warning("No OTP request found for %s", email)
                raise InvalidOTPException(
                    "No OTP request found for this email.",
                    status_code=status.HTTP_404_NOT_FOUND,
                    error_code="OTP_NOT_FOUND",
                )

            logger.info("Stored OTP: %s", record["otp"])
            logger.info("Received OTP: %s", otp)

            # Check expiry
            if datetime.now(UTC) > record["expires_at"]:
                otp_repository.delete_otp(email)

                logger.warning("OTP expired for %s", email)

                raise ExpiredOTPException("OTP has expired.")

            # Check maximum attempts
            if record["attempts"] >= settings.OTP_MAX_ATTEMPTS:
                otp_repository.delete_otp(email)

                logger.warning("Maximum OTP attempts exceeded for %s", email)

                raise BaseAppException(
                    "Maximum OTP verification attempts exceeded.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    error_code="TOO_MANY_ATTEMPTS",
                )

            # Incorrect OTP
            if record["otp"] != otp:
                record["attempts"] += 1

                logger.warning(
                    "Invalid OTP attempt %d for %s",
                    record["attempts"],
                    email,
                )

                if record["attempts"] >= settings.OTP_MAX_ATTEMPTS:
                    otp_repository.delete_otp(email)

                    logger.warning(
                        "OTP deleted after maximum failed attempts for %s",
                        email,
                    )

                raise InvalidOTPException("Invalid OTP.")

            # Success
            otp_repository.delete_otp(email)

            logger.info("OTP verified successfully for %s", email)

            return True


otp_service = OTPService()
