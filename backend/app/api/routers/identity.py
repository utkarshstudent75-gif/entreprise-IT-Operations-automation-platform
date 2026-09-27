from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import check_role
from app.core.exceptions import BaseAppException
from app.database.dependencies import get_db
from app.schemas.identity import (
    AccountUnlockRequestCreate,
    AccountUnlockRequestRead,
)
from app.schemas.response import StandardResponse
from app.services.audit_service import audit_service
from app.services.identity_service import identity_service

router = APIRouter(
    prefix="/identity",
    tags=["Identity Operations"],
)

EMPLOYEE_AND_APPROVER_ROLES = [
    "Standard User",
    "Platform Administrator",
    "Support Engineer",
]
APPROVER_ROLES = ["Platform Administrator", "Support Engineer"]


@router.post(
    "/unlock-requests",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=StandardResponse[AccountUnlockRequestRead],
)
def request_account_unlock(
    request: AccountUnlockRequestCreate,
    current_user: Annotated[
        dict[str, Any], Depends(check_role(EMPLOYEE_AND_APPROVER_ROLES))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    if request.email.casefold() != current_user["email"].casefold():
        audit_service.record_event(
            action="account_unlock_requested",
            status="FAILED",
            details={
                "requester_email": current_user["email"],
                "reason": "identity_verification_failed",
            },
        )
        raise BaseAppException(
            "Identity verification failed.",
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="IDENTITY_VERIFICATION_FAILED",
        )
    created = identity_service.create_unlock_request(
        db,
        current_user["email"],
        request.justification,
    )
    return StandardResponse(data=created)


@router.get(
    "/unlock-requests/mine",
    response_model=StandardResponse[list[AccountUnlockRequestRead]],
)
def get_my_unlock_requests(
    current_user: Annotated[
        dict[str, Any], Depends(check_role(EMPLOYEE_AND_APPROVER_ROLES))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    requests = identity_service.list_unlock_requests(
        db, requester_email=current_user["email"]
    )
    return StandardResponse(data=requests)


@router.get(
    "/unlock-requests/pending",
    response_model=StandardResponse[list[AccountUnlockRequestRead]],
)
def get_pending_unlock_requests(
    _: Annotated[dict[str, Any], Depends(check_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
):
    requests = identity_service.list_unlock_requests(db)
    return StandardResponse(data=requests)
