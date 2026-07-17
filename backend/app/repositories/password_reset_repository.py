from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.password_reset_request import PasswordResetRequest


class PasswordResetRepository:
    """Database operations for password reset requests."""

    def create_reset_request(
        self,
        db: Session,
        user_id: int,
        otp: str,
        expires_at: datetime,
    ) -> PasswordResetRequest:
        """Create and persist a new PasswordResetRequest record."""
        reset_request = PasswordResetRequest(
            user_id=user_id,
            otp=otp,
            expires_at=expires_at,
        )
        db.add(reset_request)
        db.commit()
        db.refresh(reset_request)
        return reset_request

    def get_latest_request(
        self,
        db: Session,
        user_id: int,
    ) -> PasswordResetRequest | None:
        """Return the newest password reset request for a user.

        This method does not evaluate expiry or usage state because the service
        layer manages those rules.
        """
        statement = (
            select(PasswordResetRequest)
            .where(PasswordResetRequest.user_id == user_id)
            .order_by(PasswordResetRequest.created_at.desc())
            .limit(1)
        )
        result = db.execute(statement).scalar_one_or_none()
        return result

    def get_latest_valid_request(
        self,
        db: Session,
        user_id: int,
    ) -> PasswordResetRequest | None:
        """Return the newest unused password reset request for a user.

        This method does not evaluate expiry because expiry checks belong in the
        service layer.
        """
        statement = (
            select(PasswordResetRequest)
            .where(
                PasswordResetRequest.user_id == user_id,
                PasswordResetRequest.is_used.is_(False),
            )
            .order_by(PasswordResetRequest.created_at.desc())
            .limit(1)
        )
        result = db.execute(statement).scalar_one_or_none()
        return result

    def mark_used(
        self,
        db: Session,
        reset_request: PasswordResetRequest,
    ) -> PasswordResetRequest:
        """Mark a password reset request as used and persist the change."""
        reset_request.is_used = True
        db.add(reset_request)
        db.commit()
        db.refresh(reset_request)
        return reset_request

    def delete_expired_requests(self, db: Session) -> None:
        """Delete requests that are past their expiry timestamp."""
        statement = delete(PasswordResetRequest).where(
            PasswordResetRequest.expires_at < datetime.utcnow()
        )
        db.execute(statement)
        db.commit()


password_reset_repository = PasswordResetRepository()
