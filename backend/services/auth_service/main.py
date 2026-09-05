# ruff: noqa: E402
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.admin import router as admin_router
from app.api.routers.auth import router as auth_router
from app.api.routers.mfa import router as mfa_router
from app.api.routers.password_reset import router as password_router
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.core.context import action, request_id, request_ip, request_user_agent, user_id
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import logger, setup_logging
from app.core.redis import redis_manager

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_manager.init_redis()
    if await redis_manager.ping():
        logger.info("Auth Service: Redis Connected")
    else:
        logger.error("Auth Service: Redis Connection Failed")
    yield
    await redis_manager.close()


app = FastAPI(
    title="EITOAP Auth Microservice",
    description="Identity verification, authentication, user management, and password reset microservice.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.middleware("http")
async def add_audit_context_middleware(request: Request, call_next):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    ip = (
        x_forwarded_for.split(",")[0].strip()
        if x_forwarded_for
        else (request.client.host if request.client else None)
    )
    user_agent = request.headers.get("user-agent")
    req_id = request.headers.get("x-request-id") or str(uuid.uuid4())

    token_ip = request_ip.set(ip)
    token_ua = request_user_agent.set(user_agent)
    token_rid = request_id.set(req_id)
    token_uid = user_id.set(None)
    token_act = action.set(None)

    try:
        response = await call_next(request)
        response.headers["x-request-id"] = req_id
        return response
    finally:
        request_ip.reset(token_ip)
        request_user_agent.reset(token_ua)
        request_id.reset(token_rid)
        user_id.reset(token_uid)
        action.reset(token_act)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(password_router, prefix="/api/v1")
app.include_router(mfa_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
