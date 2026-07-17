from fastapi import APIRouter

from app.api.v1.audit import router as audit_router
from app.api.v1.health import router as health_router
from app.api.v1.password import router as password_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(password_router)
api_router.include_router(users_router)
api_router.include_router(audit_router)
