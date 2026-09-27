from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.account_unlock_request import AccountUnlockRequest
from app.models.user import User
from app.services.audit_service import audit_service
from app.services.graph_service import GraphAPIException, graph_service


class IdentityService:
    def create_unlock_request(
        self,
        db: Session,
        requester_email: str,
        justification: str,
    ) -> AccountUnlockRequest:
        normalized_email = requester_email.casefold()
        user = (
            db.query(User)
            .filter(func.lower(User.email) == normalized_email)
            .one_or_none()
        )
        request = AccountUnlockRequest(
            requested_by=user.id if user else None,
            requester_email=normalized_email,
            justification=justification,
            status="PENDING",
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        audit_service.record_event(
            action="account_unlock_requested",
            status="SUCCESS",
            user_id=user.id if user else None,
            details={
                "request_id": request.id,
                "requester_email": normalized_email,
                "status": request.status,
                "processing": "manual",
            },
        )
        logger.info("Account unlock request recorded for manual processing.")
        return request

    async def reset_mfa(self, email: str) -> int:
        normalized_email = email.casefold()
        try:
            methods_removed = await graph_service.reset_mfa_methods(normalized_email)
        except GraphAPIException as exc:
            audit_service.record_event(
                action="mfa_reset",
                status="FAILED",
                details={
                    "email": normalized_email,
                    "reason": exc.error_code,
                },
            )
            raise

        audit_service.record_event(
            action="mfa_reset",
            status="SUCCESS",
            details={
                "email": normalized_email,
                "methods_removed": methods_removed,
            },
        )
        return methods_removed

    def list_unlock_requests(
        self, db: Session, requester_email: str | None = None
    ) -> list[AccountUnlockRequest]:
        query = db.query(AccountUnlockRequest)
        if requester_email is not None:
            query = query.filter(
                AccountUnlockRequest.requester_email == requester_email.casefold()
            )
        return query.order_by(AccountUnlockRequest.created_at.desc()).all()


identity_service = IdentityService()
