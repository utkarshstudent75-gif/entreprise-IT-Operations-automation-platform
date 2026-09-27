from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.logging_config import logger
from app.core.rate_limiter import rate_limiter
from app.database.dependencies import get_db
from app.schemas.password import (
    ForgotPasswordRequest,
    PasswordResponse,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from app.schemas.response import ErrorResponse, StandardResponse
from app.services.audit_service import audit_service
from app.services.password_reset_service import password_reset_service

router = APIRouter(
    prefix="/password",
    tags=["Password"],
)

DUMMY_REQUEST_ID = "f8a9e88d-cf7d-417d-815f-6a75a7c2be5f"
DUMMY_REQUEST_ID_2 = "e4f8a9e8-cf7d-417d-815f-6a75a7c2be5f"


async def check_cooldown(email: str, ip: str) -> None:
    """Checks if the email or IP is currently blocked due to excessive failures."""
    from app.core.redis import get_redis

    try:
        redis_client = await get_redis()
        blocked_email = await redis_client.get(f"block:otp:{email}")
        blocked_ip = await redis_client.get(f"block:ip:{ip}")
        if blocked_email or blocked_ip:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again after 15 minutes.",
            )
    except HTTPException:
        raise
    except Exception:  # nosec B110
        pass


async def record_failure(email: str, ip: str) -> None:
    """Increments failure counts and triggers blocking cooldown on 5 failures."""
    from app.core.redis import get_redis

    try:
        redis_client = await get_redis()

        # Track failures for 15 minutes (900 seconds)
        fails = await redis_client.incr(f"fail:otp:{email}")
        await redis_client.expire(f"fail:otp:{email}", 900)

        ip_fails = await redis_client.incr(f"fail:ip:{ip}")
        await redis_client.expire(f"fail:ip:{ip}", 900)

        if fails >= 5:
            await redis_client.set(f"block:otp:{email}", "1", ex=900)
            logger.warning(
                "Email %s blocked from password resets for 15 minutes due to excessive failures.",
                email,
            )
        if ip_fails >= 5:
            await redis_client.set(f"block:ip:{ip}", "1", ex=900)
            logger.warning(
                "IP %s blocked from password resets for 15 minutes due to excessive failures.",
                ip,
            )
    except Exception:  # nosec B110
        pass


async def clear_failures(email: str, ip: str) -> None:
    """Resets the failure counters on successful OTP authentication."""
    from app.core.redis import get_redis

    try:
        redis_client = await get_redis()
        await redis_client.delete(f"fail:otp:{email}")
        await redis_client.delete(f"fail:ip:{ip}")
    except Exception:  # nosec B110
        pass


@router.post(
    "/forgot-password",
    response_model=StandardResponse[PasswordResponse],
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    description=(
        "Initiates the password reset flow. If the account with the "
        "provided email exists, a reset code (OTP) will be generated "
        "and sent to the business phone number associated with their profile in Entra ID. "
        "To prevent user enumeration and maintain "
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
    await password_reset_service.request_password_reset(db, request.email)

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
        "user's business phone number in Entra ID. This step does not consume or invalidate the OTP; it "
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
    request: VerifyOtpRequest, req_obj: Request, db: Annotated[Session, Depends(get_db)]
):
    ip = req_obj.client.host if req_obj.client else "unknown"
    await check_cooldown(request.email, ip)

    rate_limiter.check_limit(
        key=f"verify-otp:{request.email}",
        limit=10,
        window_seconds=600,
    )

    try:
        await password_reset_service.verify_otp(db, request.email, request.otp)
        await clear_failures(request.email, ip)
    except Exception:
        await record_failure(request.email, ip)
        raise

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
    request: ResetPasswordRequest,
    req_obj: Request,
    db: Annotated[Session, Depends(get_db)],
):
    ip = req_obj.client.host if req_obj.client else "unknown"
    await check_cooldown(request.email, ip)

    try:
        await password_reset_service.reset_password(
            db,
            request.email,
            request.otp,
            request.new_password,
            confirm_password=request.confirm_password,
        )
        await clear_failures(request.email, ip)
    except Exception:
        await record_failure(request.email, ip)
        raise

    return StandardResponse(
        data=PasswordResponse(message="Password has been reset successfully.")
    )


@router.get(
    "/policy",
    status_code=status.HTTP_200_OK,
)
async def get_password_policy():
    """
    Exposes password complexity settings to the frontend.
    """
    return StandardResponse(
        data={
            "min_length": settings.PASSWORD_MIN_LENGTH,
            "require_uppercase": settings.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": settings.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": settings.PASSWORD_REQUIRE_NUMBERS,
            "require_special": settings.PASSWORD_REQUIRE_SPECIAL,
        }
    )


@router.get(
    "/reset-history",
    status_code=status.HTTP_200_OK,
)
async def get_reset_history(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Retrieves the password reset logs.
    Admins, Auditors, and Support can view all logs. Standard users can only view their own.
    """
    logs = audit_service.list_logs(db, limit=500)

    reset_actions = [
        "forgot_password",
        "otp_verification",
        "password_reset",
        "graph_password_reset_initiated",
        "graph_password_reset_successful",
        "graph_password_reset_failed",
    ]

    filtered_logs = []
    for log in logs:
        if log.action not in reset_actions:
            continue

        email_detail = log.details.get("email") if log.details else None

        # Check permissions and filter accordingly
        if current_user["role"] in [
            "Platform Administrator",
            "Auditor",
            "Support Engineer",
        ]:
            filtered_logs.append(
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "status": log.status,
                    "ip_address": log.ip_address,
                    "request_id": log.request_id,
                    "details": log.details,
                }
            )
        elif email_detail == current_user["email"]:
            filtered_logs.append(
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "status": log.status,
                    "ip_address": log.ip_address,
                    "request_id": log.request_id,
                    "details": log.details,
                }
            )

    return StandardResponse(data=filtered_logs)
