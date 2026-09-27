from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import check_role
from app.database.dependencies import get_db
from app.schemas.response import StandardResponse
from app.schemas.software_request import (
    SoftwareDecision,
    SoftwareRequestCreate,
    SoftwareRequestRead,
)
from app.services.software_request_service import software_request_service

router = APIRouter(
    prefix="/software",
    tags=["Software Requests"],
)

EMPLOYEE_AND_APPROVER_ROLES = [
    "Standard User",
    "Platform Administrator",
    "Support Engineer",
]
APPROVER_ROLES = ["Platform Administrator", "Support Engineer"]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[SoftwareRequestRead],
)
def create_software_request(
    request: SoftwareRequestCreate,
    current_user: Annotated[
        dict[str, Any], Depends(check_role(EMPLOYEE_AND_APPROVER_ROLES))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    created = software_request_service.create_request(
        db, current_user["email"], request
    )
    return StandardResponse(data=created)


@router.get(
    "/mine",
    response_model=StandardResponse[list[SoftwareRequestRead]],
)
def get_my_software_requests(
    current_user: Annotated[
        dict[str, Any], Depends(check_role(EMPLOYEE_AND_APPROVER_ROLES))
    ],
    db: Annotated[Session, Depends(get_db)],
):
    requests = software_request_service.list_requests(
        db, requester_email=current_user["email"]
    )
    return StandardResponse(data=requests)


@router.get(
    "/pending",
    response_model=StandardResponse[list[SoftwareRequestRead]],
)
def get_pending_software_requests(
    current_user: Annotated[dict[str, Any], Depends(check_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
):
    requests = software_request_service.list_requests(db, pending=True)
    return StandardResponse(data=requests)


@router.post(
    "/{request_id}/approve",
    response_model=StandardResponse[SoftwareRequestRead],
)
async def approve_software_request(
    request_id: int,
    current_user: Annotated[dict[str, Any], Depends(check_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    decision: SoftwareDecision | None = None,
):
    request = await software_request_service.decide_request(
        db,
        request_id,
        current_user["email"],
        "APPROVED",
        decision.note if decision else None,
    )
    return StandardResponse(data=request)


@router.post(
    "/{request_id}/reject",
    response_model=StandardResponse[SoftwareRequestRead],
)
async def reject_software_request(
    request_id: int,
    current_user: Annotated[dict[str, Any], Depends(check_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    decision: SoftwareDecision | None = None,
):
    request = await software_request_service.decide_request(
        db,
        request_id,
        current_user["email"],
        "REJECTED",
        decision.note if decision else None,
    )
    return StandardResponse(data=request)
