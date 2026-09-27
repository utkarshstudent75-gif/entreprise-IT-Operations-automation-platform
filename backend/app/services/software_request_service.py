from datetime import UTC, datetime

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.core.exceptions import BaseAppException, NotificationException
from app.core.logging_config import logger
from app.models.software_request import SoftwareRequest
from app.models.user import User
from app.schemas.sms import SmsRequest
from app.schemas.software_request import SoftwareRequestCreate
from app.services.audit_service import audit_service
from app.services.graph_service import graph_service
from app.services.notification_service import notification_service


class SoftwareRequestService:
    def create_request(
        self, db: Session, requester_email: str, request_data: SoftwareRequestCreate
    ) -> SoftwareRequest:
        normalized_email = requester_email.casefold()
        user = (
            db.query(User)
            .filter(func.lower(User.email) == normalized_email)
            .one_or_none()
        )
        request = SoftwareRequest(
            software_name=request_data.software_name.strip(),
            reason=request_data.justification.strip(),
            status="PENDING",
            requested_by=user.id if user else None,
            requester_email=normalized_email,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        audit_service.record_event(
            action="software_request_created",
            status="SUCCESS",
            user_id=user.id if user else None,
            details={
                "request_id": request.id,
                "requester_email": normalized_email,
                "software_name": request.software_name,
            },
        )
        return request

    def list_requests(
        self, db: Session, requester_email: str | None = None, pending: bool = False
    ) -> list[SoftwareRequest]:
        query = db.query(SoftwareRequest)
        if requester_email is not None:
            query = query.filter(
                SoftwareRequest.requester_email == requester_email.casefold()
            )
        if pending:
            query = query.filter(SoftwareRequest.status == "PENDING")
        return query.order_by(SoftwareRequest.created_at.desc()).all()

    async def decide_request(
        self,
        db: Session,
        request_id: int,
        approver_email: str,
        decision: str,
        note: str | None = None,
    ) -> SoftwareRequest:
        normalized_approver = approver_email.casefold()
        now = datetime.now(UTC).replace(tzinfo=None)
        result = db.execute(
            update(SoftwareRequest)
            .where(
                SoftwareRequest.id == request_id,
                SoftwareRequest.status == "PENDING",
            )
            .values(
                status=decision,
                decided_by_email=normalized_approver,
                decision_note=note.strip() if note and note.strip() else None,
                decided_at=now,
                updated_at=now,
            )
        )
        if result.rowcount != 1:
            request = (
                db.query(SoftwareRequest)
                .filter(SoftwareRequest.id == request_id)
                .one_or_none()
            )
            if request is None:
                raise BaseAppException(
                    "Software request not found.",
                    status_code=404,
                    error_code="SOFTWARE_REQUEST_NOT_FOUND",
                )
            raise BaseAppException(
                "This software request has already been decided.",
                status_code=409,
                error_code="SOFTWARE_REQUEST_ALREADY_DECIDED",
            )

        db.commit()
        request = (
            db.query(SoftwareRequest).filter(SoftwareRequest.id == request_id).one()
        )
        action = f"software_request_{decision.casefold()}"
        audit_service.record_event(
            action=action,
            status="SUCCESS",
            details={
                "request_id": request.id,
                "requester_email": request.requester_email,
                "software_name": request.software_name,
                "approver_email": normalized_approver,
                "status": decision,
            },
        )
        await self._notify_requester(request)
        return request

    async def _notify_requester(self, request: SoftwareRequest) -> None:
        try:
            phone_number = await graph_service.get_user_phone(
                request.requester_email or ""
            )
            if not phone_number:
                raise NotificationException(
                    "No registered notification destination is available."
                )
            notification_service.send_sms(
                SmsRequest(
                    phone_number=phone_number,
                    message=(
                        f"Your software request for {request.software_name} was "
                        f"{request.status.casefold()}."
                    ),
                )
            )
        except BaseAppException as exc:
            audit_service.record_event(
                action="software_request_notification",
                status="FAILED",
                details={"request_id": request.id, "reason": exc.error_code},
            )
            logger.error("Software request decision was saved but notification failed.")
            raise BaseAppException(
                "The decision was saved, but the requester notification could not be delivered.",
                status_code=502,
                error_code="REQUEST_NOTIFICATION_FAILED",
            ) from exc

        audit_service.record_event(
            action="software_request_notification",
            status="SUCCESS",
            details={"request_id": request.id},
        )


software_request_service = SoftwareRequestService()
