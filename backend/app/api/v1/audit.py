from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import BaseAppException
from app.database.dependencies import get_db
from app.schemas.audit import AuditLogResponse
from app.schemas.response import StandardResponse
from app.services.audit_service import audit_service

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=StandardResponse[list[AuditLogResponse]],
    status_code=status.HTTP_200_OK,
)
def get_audit_logs(
    user_id: int | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by audit action"),
    status: str | None = Query(None, description="Filter by status (SUCCESS/FAILED)"),
    start_date: datetime | None = Query(
        None, description="Filter logs on or after this timestamp (UTC)"
    ),
    end_date: datetime | None = Query(
        None, description="Filter logs on or before this timestamp (UTC)"
    ),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of logs to return"),
    db: Session = Depends(get_db),
):
    """Retrieve audit logs with optional filtering by user ID, action, status,
    and date range.
    """
    logs = audit_service.list_logs(
        db=db,
        user_id=user_id,
        action=action,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return StandardResponse(data=logs)


@router.get(
    "/{audit_id}",
    response_model=StandardResponse[AuditLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_audit_log(
    audit_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single audit log entry by its ID."""
    log = audit_service.get_log_by_id(db, audit_id)
    if log is None:
        raise BaseAppException(
            "Audit log not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="AUDIT_LOG_NOT_FOUND",
        )
    return StandardResponse(data=log)
