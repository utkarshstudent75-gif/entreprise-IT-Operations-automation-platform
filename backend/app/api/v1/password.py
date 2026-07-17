from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.password import (
    ForgotPasswordRequest,
    PasswordResponse,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from app.services.password_reset_service import (
    PasswordResetAlreadyUsedError,
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)

router = APIRouter(
    prefix="/password",
    tags=["Password"],
)


@router.post(
    "/forgot-password",
    response_model=PasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    password_reset_service.request_password_reset(db, request.email)

    return PasswordResponse(
        message="If the account exists, a reset code has been sent."
    )


@router.post(
    "/verify-otp",
    response_model=PasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    try:
        password_reset_service.verify_otp(db, request.email, request.otp)
    except (
        PasswordResetInvalidRequest,
        PasswordResetExpiredError,
        PasswordResetAlreadyUsedError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return PasswordResponse(message="OTP verified successfully.")


@router.post(
    "/reset-password",
    response_model=PasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        password_reset_service.reset_password(
            db,
            request.email,
            request.otp,
            request.new_password,
        )
    except PasswordResetExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc))
    except (
        PasswordResetInvalidRequest,
        PasswordResetAlreadyUsedError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return PasswordResponse(message="Password has been reset successfully.")
    