from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.logging_config import logger


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning("HTTP %s - %s (%s)", exc.status_code, exc.detail, request.url.path,)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "message": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled Exception while processing %s", request.url.path,)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status_code": 500,
                "message": "Internal Server Error",
            },
        )