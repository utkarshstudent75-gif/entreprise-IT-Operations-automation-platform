from datetime import datetime
from typing import Any
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    """Database operations for AuditLog records."""

    def create_entry(
        self,
        db: Session,
        action: str,
        status: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditLog:
        """Create and persist a new AuditLog record."""
        audit_log = AuditLog(
            action=action,
            status=status,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details,
        )
        if timestamp:
            audit_log.timestamp = timestamp

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    def get_by_id(self, db: Session, audit_id: int) -> AuditLog | None:
        """Fetch a single AuditLog by its ID."""
        statement = select(AuditLog).where(AuditLog.id == audit_id)
        return db.execute(statement).scalar_one_or_none()

    def get_all(
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
        """Fetch audit logs matching the given filters, ordered by timestamp descending."""
        statement = select(AuditLog)

        if user_id is not None:
            statement = statement.where(AuditLog.user_id == user_id)
        if action is not None:
            statement = statement.where(AuditLog.action == action)
        if status is not None:
            statement = statement.where(AuditLog.status == status)
        if start_date is not None:
            statement = statement.where(AuditLog.timestamp >= start_date)
        if end_date is not None:
            statement = statement.where(AuditLog.timestamp <= end_date)

        statement = statement.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)
        return list(db.execute(statement).scalars().all())


audit_repository = AuditRepository()
