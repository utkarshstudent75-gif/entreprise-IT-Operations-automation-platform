from fastapi import APIRouter

from app.schemas.password import (
    ForgotPasswordRequest,
    VerifyOtpRequest,
)
from app.services.otp_service import otp_service
from app.services.password_service import password_service

router = APIRouter(
    prefix="/password",
    tags=["Password"],
)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):

    password_service.request_password_reset(request.email)

    return {
        "message": "If the account exists, a verification code has been sent."
    }


@router.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest):

    otp_service.verify_otp(
        request.email,
        request.otp,
    )

    
    return {
            "message": "OTP verified successfully."
        }

    