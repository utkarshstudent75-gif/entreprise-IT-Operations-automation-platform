from fastapi import FastAPI

from app.api.v1.router import api_router

from app.core.config import settings

app = FastAPI(
        title=settings.APP_NAME,
        description="Enterprise-grade IT Helpdesk Automation Platform",
        version=settings.APP_VERSION,
 )


app.include_router(api_router, prefix="/api/v1")

