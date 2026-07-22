from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logging_config import logger
from app.database.session import SessionLocal
from app.schemas.health import HealthResponse, LiveResponse, ReadyResponse
from app.schemas.response import ErrorResponse, StandardResponse

router = APIRouter()


def check_db_health() -> bool:
    """
    Utility function to verify PostgreSQL connectivity.
    Executes a simple 'SELECT 1' query and returns True on success, False on failure.
    """
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connectivity check failed: %s", str(e), exc_info=True)
        return False
    finally:
        db.close()


@router.get("/health", tags=["Health"], response_model=StandardResponse[HealthResponse])
async def health_check():
    """
    Health check endpoint.
    Returns the general application status, service name, and version.
    """
    return StandardResponse(
        data=HealthResponse(
            status="healthy",
            service=settings.APP_NAME,
            version=settings.APP_VERSION,
        )
    )


async def check_redis_health_async() -> bool:
    from app.core.redis import redis_manager

    return await redis_manager.ping()


def check_sms_health() -> bool:
    """
    Utility function to verify SMS notification provider readiness.
    Does not send real SMS messages during health checks.
    """
    from app.services.notification_service import notification_service

    try:
        return notification_service.is_ready()
    except Exception as e:
        logger.error("SMS provider health check failed: %s", str(e), exc_info=True)
        return False


@router.get(
    "/ready",
    tags=["Health"],
    response_model=StandardResponse[ReadyResponse],
    responses={503: {"model": ErrorResponse}},
)
async def ready_check():
    """
    Readiness check endpoint.
    Verifies connectivity to PostgreSQL database, Redis, and SMS Provider readiness.
    Returns HTTP 503 Service Unavailable if any dependent service is unhealthy.
    """
    db_healthy = check_db_health()
    redis_healthy = await check_redis_health_async()
    sms_healthy = check_sms_health()

    if not db_healthy or not redis_healthy or not sms_healthy:
        failed_services = []
        if not db_healthy:
            failed_services.append("Database")
        if not redis_healthy:
            failed_services.append("Redis")
        if not sms_healthy:
            failed_services.append("SMS Provider")

        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": f"connection failed for: {', '.join(failed_services)}",
                },
            },
        )

    return StandardResponse(
        data=ReadyResponse(
            status="ready",
            database="connected",
            redis="connected",
            application="healthy",
            sms_provider="connected",
        )
    )


@router.get("/live", tags=["Health"], response_model=StandardResponse[LiveResponse])
async def live_check():
    """
    Liveness check endpoint.
    Verifies that the application process is alive and responsive.
    """
    return StandardResponse(
        data=LiveResponse(
            status="alive",
        )
    )
