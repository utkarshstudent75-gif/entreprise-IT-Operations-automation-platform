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


def check_redis_health() -> bool:
    """
    Utility function to verify Redis connectivity.
    """
    # Import inside to avoid circular dependencies

    try:
        # Run the async ping in a synchronous context or simply check via an async endpoint.
        # But wait, health check endpoint is async, so we can just make check_redis_health async!
        pass
    except Exception:
        return False


async def check_redis_health_async() -> bool:
    from app.core.redis import redis_manager

    return await redis_manager.ping()


@router.get(
    "/ready",
    tags=["Health"],
    response_model=StandardResponse[ReadyResponse],
    responses={503: {"model": ErrorResponse}},
)
async def ready_check():
    """
    Readiness check endpoint.
    Verifies connectivity to the PostgreSQL database and Redis.
    Returns HTTP 503 Service Unavailable if either database or Redis is down.
    """
    db_healthy = check_db_health()
    redis_healthy = await check_redis_health_async()

    if not db_healthy or not redis_healthy:
        failed_services = []
        if not db_healthy:
            failed_services.append("Database")
        if not redis_healthy:
            failed_services.append("Redis")

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
