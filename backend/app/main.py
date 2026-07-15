from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

from app.core.config import settings


from app.core.exception_handlers import register_exception_handlers
app = FastAPI(
        title=settings.APP_NAME,
        description="Enterprise-grade IT Helpdesk Automation Platform",
        version=settings.APP_VERSION,
 )
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


app.include_router(api_router, prefix="/api/v1")
