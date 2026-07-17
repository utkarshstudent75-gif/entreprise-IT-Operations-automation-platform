from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.context import request_id, request_ip, request_user_agent
from app.core.logging_config import logger
from app.database.session import SessionLocal
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import audit_repository


class AuditService:
    """Handles logging of audit events with resiliency."""

    def record_event(
        self,
        action: str,
        status: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id_val: str | None = None,
        details: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditLog | None:
        """Record an audit log entry.

        This method will resolve client details from request context variables if not
        explicitly provided, and will perform the database write using a dedicated
        database session. Any exceptions raised during the database operation will be
        logged and swallowed, ensuring audit failures never impact business logic.
        """
        # Resolve values from request context if not explicitly provided
        resolved_ip = ip_address or request_ip.get()
        resolved_ua = user_agent or request_user_agent.get()
        resolved_rid = request_id_val or request_id.get()

        # Execute using a fresh session to keep the transaction isolated
        session = SessionLocal()
        try:
            audit_log = audit_repository.create_entry(
                db=session,
                action=action,
                status=status,
                user_id=user_id,
                ip_address=resolved_ip,
                user_agent=resolved_ua,
                request_id=resolved_rid,
                details=details,
                timestamp=timestamp,
            )
            return audit_log
        except Exception as e:
            # Swallowed to guarantee resiliency of primary business flow
            logger.error(
                "Audit log recording failed for action '%s', status '%s': %s",
                action,
                status,
                str(e),
                exc_info=True,
            )
            return None
        finally:
            session.close()

    def get_log_by_id(self, db: Session, audit_id: int) -> AuditLog | None:
        """Fetch audit log by ID (delegates to repository)."""
        return audit_repository.get_by_id(db, audit_id)

    def list_logs(
        self,
        db: Session,
        user_id: int | None = None,
        action: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Fetch filtered audit logs (delegates to repository)."""
        return audit_repository.get_all(
            db=db,
            user_id=user_id,
            action=action,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )


audit_service = AuditService()
