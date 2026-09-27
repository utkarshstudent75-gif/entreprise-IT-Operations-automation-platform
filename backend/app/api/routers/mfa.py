from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.auth.dependencies import check_role
from app.core.exceptions import BaseAppException
from app.schemas.identity import MFAResetRequest, MFAResetResult
from app.schemas.response import StandardResponse
from app.services.audit_service import audit_service
from app.services.identity_service import identity_service

router = APIRouter(
    prefix="/mfa",
    tags=["MFA"],
)

MFA_ROLES = ["Standard User", "Platform Administrator", "Support Engineer"]


@router.post(
    "/reset",
    status_code=http_status.HTTP_200_OK,
    response_model=StandardResponse[MFAResetResult],
)
async def reset_mfa(
    request: MFAResetRequest,
    current_user: Annotated[dict[str, Any], Depends(check_role(MFA_ROLES))],
):
    if request.email.casefold() != current_user["email"].casefold():
        audit_service.record_event(
            action="mfa_reset",
            status="FAILED",
            details={
                "email": current_user["email"],
                "reason": "identity_verification_failed",
            },
        )
        raise BaseAppException(
            "Identity verification failed.",
            status_code=http_status.HTTP_403_FORBIDDEN,
            error_code="IDENTITY_VERIFICATION_FAILED",
        )

    methods_removed = await identity_service.reset_mfa(current_user["email"])
    return StandardResponse(
        data=MFAResetResult(
            message="Your authentication methods have been reset.",
            methods_removed=methods_removed,
        )
    )
