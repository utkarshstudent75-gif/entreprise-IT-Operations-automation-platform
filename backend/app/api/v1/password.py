from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.response import StandardResponse
from app.schemas.password import (
    ForgotPasswordRequest,
    PasswordResponse,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from app.services.password_reset_service import password_reset_service
from app.core.rate_limiter import rate_limiter

router = APIRouter(
    prefix="/password",
    tags=["Password"],
)


@router.post(
    "/forgot-password",
    response_model=StandardResponse[PasswordResponse],
    status_code=status.HTTP_200_OK,
)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    rate_limiter.check_limit(
        key=f"forgot-password:{request.email}",
        limit=5,
        window_seconds=600,
    )
    password_reset_service.request_password_reset(db, request.email)

    return StandardResponse(
        data=PasswordResponse(
            message="If the account exists, a reset code has been sent."
        )
    )


@router.post(
    "/verify-otp",
    response_model=StandardResponse[PasswordResponse],
    status_code=status.HTTP_200_OK,
)
async def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    rate_limiter.check_limit(
        key=f"verify-otp:{request.email}",
        limit=10,
        window_seconds=600,
    )
    password_reset_service.verify_otp(db, request.email, request.otp)
    return StandardResponse(data=PasswordResponse(message="OTP verified successfully."))



@router.post(
    "/reset-password",
    response_model=StandardResponse[PasswordResponse],
    status_code=status.HTTP_200_OK,
)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    password_reset_service.reset_password(
        db,
        request.email,
        request.otp,
        request.new_password,
    )
    return StandardResponse(data=PasswordResponse(message="Password has been reset successfully."))

    