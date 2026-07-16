import secrets
from datetime import datetime

from fastapi import HTTPException, status

from app.core.config import settings
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

        otp = "".join(
            str(secrets.randbelow(10))
            for _ in range(settings.OTP_LENGTH)
        )

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

        record = otp_repository.get_otp(email)

        if record is None:
            logger.warning("No OTP request found for %s", email)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No OTP request found for this email.",
            )

        logger.info("Stored OTP: %s", record["otp"])
        logger.info("Received OTP: %s", otp)

        # Check expiry
        if datetime.utcnow() > record["expires_at"]:
            otp_repository.delete_otp(email)

            logger.warning("OTP expired for %s", email)

            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="OTP has expired.",
            )

        # Check maximum attempts
        if record["attempts"] >= settings.OTP_MAX_ATTEMPTS:
            otp_repository.delete_otp(email)

            logger.warning("Maximum OTP attempts exceeded for %s", email)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum OTP verification attempts exceeded.",
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

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP.",
            )

        # Success
        otp_repository.delete_otp(email)

        logger.info("OTP verified successfully for %s", email)

        return True


otp_service = OTPService()