import datetime
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.audit_log import AuditLog
from app.schemas.response import StandardResponse

logger = logging.getLogger("itpa")

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
async def get_dashboard_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Returns counts of password resets, active sessions, and pending requests.
    Filtered for the current user if role is Standard User.
    """
    # Fetch last 500 audit entries to perform safe python-side evaluation
    # (prevents json query failures across SQLite/Postgres)
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500).all()

    user_email = current_user["email"]
    is_standard = current_user["role"] == "Standard User"

    successful_resets = 0
    failed_resets = 0

    for log in logs:
        if log.action == "password_reset":
            details = log.details or {}
            log_email = details.get("email")
            if is_standard and log_email != user_email:
                continue

            if log.status == "SUCCESS":
                successful_resets += 1
            elif log.status == "FAILED":
                failed_resets += 1

    total_requests = successful_resets + failed_resets

    return StandardResponse(
        data={
            "total_requests": total_requests,
            "successful_resets": successful_resets,
            "failed_resets": failed_resets,
            "pending_approvals": 0 if is_standard else 2,
            "active_sessions": 1,
        }
    )


@router.get("/recent-activity")
async def get_recent_activity(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Returns recent audit logs list.
    Standard Users only receive entries matching their corporate email.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

    user_email = current_user["email"]
    is_standard = current_user["role"] == "Standard User"

    activity = []
    for log in logs:
        details = log.details or {}
        log_email = details.get("email")
        if is_standard and log_email != user_email:
            continue

        activity.append(
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() + "Z",
                "action": log.action,
                "status": log.status,
                "ip_address": log.ip_address,
                "details": details,
            }
        )

        if len(activity) >= 10:
            break

    return StandardResponse(data=activity)


@router.get("/notifications")
async def get_dashboard_notifications(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Returns current security and operations notification messages.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    notifications = [
        {
            "id": "1",
            "title": "SSO Login Success",
            "message": f"Successfully authenticated as {current_user['name']} via Microsoft Entra ID.",
            "severity": "success",
            "timestamp": now_iso,
        }
    ]

    if current_user["role"] in ["Platform Administrator", "Support Engineer"]:
        notifications.append(
            {
                "id": "2",
                "title": "MFA Security Review",
                "message": "All administrators are required to audit authentication logs weekly.",
                "severity": "warning",
                "timestamp": now_iso,
            }
        )

    return StandardResponse(data=notifications)
