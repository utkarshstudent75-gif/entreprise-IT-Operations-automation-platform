from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.rate_limiter import rate_limiter
from app.database.dependencies import get_db
from app.schemas.password import (
    ForgotPasswordRequest,
    PasswordResponse,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from app.schemas.response import ErrorResponse, StandardResponse
from app.services.password_reset_service import password_reset_service

router = APIRouter(
    prefix="/password",
    tags=["Password"],
)

DUMMY_REQUEST_ID = "f8a9e88d-cf7d-417d-815f-6a75a7c2be5f"
DUMMY_REQUEST_ID_2 = "e4f8a9e8-cf7d-417d-815f-6a75a7c2be5f"


@router.post(
    "/forgot-password",
    response_model=StandardResponse[PasswordResponse],
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    description=(
        "Initiates the password reset flow. If the account with the "
        "provided email exists, a reset code (OTP) will be generated "
        "and logged to console. To prevent user enumeration and maintain "
        "security, a successful response (200 OK) is returned regardless "
        "of whether the email exists in the database."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Password reset OTP requested successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "message": (
                                "If the account exists, a reset code has been sent."
                            ),
                        },
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": (
                "Validation error on the request body (e.g. invalid email "
                "address format)."
            ),
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": (
                                "Validation failed: body.email: value is "
                                "not a valid email address"
                            ),
                            "request_id": DUMMY_REQUEST_ID,
                        },
                    }
                }
            },
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": (
                "Rate limit exceeded. Too many reset requests for this email address."
            ),
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "TOO_MANY_REQUESTS",
                            "message": "Rate limit exceeded. Please try again later.",
                            "request_id": DUMMY_REQUEST_ID_2,
                        },
                    }
                }
            },
        },
    },
)
async def forgot_password(
    request: ForgotPasswordRequest, db: Annotated[Session, Depends(get_db)]
):
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
    summary="Verify Password Reset OTP",
    description=(
        "Verifies the correctness and validity of the OTP code sent to the "
        "user's email. This step does not consume or invalidate the OTP; it "
        "only checks if the OTP matches, has not expired, and has not been "
        "used yet. A successful verification allows the user to proceed to "
        "the password reset endpoint."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "OTP verified successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "OTP verified successfully."},
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid OTP code or OTP already consumed/used.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_otp": {
                            "summary": "Invalid OTP code",
                            "value": {
                                "success": False,
                                "error": {
                                    "code": "INVALID_OTP",
                                    "message": "Invalid email or OTP.",
                                    "request_id": DUMMY_REQUEST_ID,
                                },
                            },
                        },
                        "otp_already_used": {
                            "summary": "OTP already used",
                            "value": {
                                "success": False,
                                "error": {
                                    "code": "OTP_ALREADY_USED",
                                    "message": "OTP has already been used.",
                                    "request_id": DUMMY_REQUEST_ID,
                                },
                            },
                        },
                    }
                }
            },
        },
        status.HTTP_410_GONE: {
            "description": "OTP has expired.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "EXPIRED_OTP",
                            "message": "OTP has expired.",
                            "request_id": DUMMY_REQUEST_ID,
                        },
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error on input fields.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": (
                                "Validation failed: body.email: value is not "
                                "a valid email address; body.otp: Field required"
                            ),
                            "request_id": DUMMY_REQUEST_ID,
                        },
                    }
                }
            },
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Rate limit exceeded. Too many verification attempts.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "TOO_MANY_REQUESTS",
                            "message": "Rate limit exceeded. Please try again later.",
                            "request_id": DUMMY_REQUEST_ID_2,
                        },
                    }
                }
            },
        },
    },
)
async def verify_otp(
    request: VerifyOtpRequest, db: Annotated[Session, Depends(get_db)]
):
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
    summary="Reset Password",
    description=(
        "Resets the user's password using the verified OTP. This operation "
        "consumes/marks the OTP as used and updates the user's password in the "
        "database in a single transaction."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Password has been reset successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"message": "Password has been reset successfully."},
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid OTP code or OTP already consumed/used.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_otp": {
                            "summary": "Invalid OTP code",
                            "value": {
                                "success": False,
                                "error": {
                                    "code": "INVALID_OTP",
                                    "message": "Invalid email or OTP.",
                                    "request_id": DUMMY_REQUEST_ID,
                                },
                            },
                        },
                        "otp_already_used": {
                            "summary": "OTP already used",
                            "value": {
                                "success": False,
                                "error": {
                                    "code": "OTP_ALREADY_USED",
                                    "message": "OTP has already been used.",
                                    "request_id": DUMMY_REQUEST_ID,
                                },
                            },
                        },
                    }
                }
            },
        },
        status.HTTP_410_GONE: {
            "description": "OTP has expired.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "EXPIRED_OTP",
                            "message": "OTP has expired.",
                            "request_id": DUMMY_REQUEST_ID,
                        },
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Validation error on input fields.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": (
                                "Validation failed: body.new_password: Field required"
                            ),
                            "request_id": DUMMY_REQUEST_ID,
                        },
                    }
                }
            },
        },
    },
)
async def reset_password(
    request: ResetPasswordRequest, db: Annotated[Session, Depends(get_db)]
):
    password_reset_service.reset_password(
        db,
        request.email,
        request.otp,
        request.new_password,
    )
    return StandardResponse(
        data=PasswordResponse(message="Password has been reset successfully.")
    )
