from fastapi import APIRouter

from app.api.routers.admin import router as admin_router
from app.api.routers.auth import router as auth_router
from app.api.routers.metrics import router as metrics_router
from app.api.routers.mfa import router as mfa_router
from app.api.routers.password_reset import router as password_router
from app.api.routers.software import router as software_router
from app.api.routers.tickets import router as tickets_router
from app.api.routers.workflows import router as workflows_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(password_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(workflows_router)
api_router.include_router(software_router)
api_router.include_router(mfa_router)
api_router.include_router(tickets_router)
api_router.include_router(metrics_router)
