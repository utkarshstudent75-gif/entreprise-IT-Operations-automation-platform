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


@router.get(
    "/ready",
    tags=["Health"],
    response_model=StandardResponse[ReadyResponse],
    responses={503: {"model": ErrorResponse}},
)
async def ready_check():
    """
    Readiness check endpoint.
    Verifies connectivity to the PostgreSQL database.
    Returns HTTP 503 Service Unavailable if database is down.
    """
    if not check_db_health():
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database connection failed",
                },
            },
        )
    return StandardResponse(
        data=ReadyResponse(
            status="ready",
            database="connected",
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
