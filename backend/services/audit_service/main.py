# ruff: noqa: E402
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.metrics import router as metrics_router
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.core.context import (
    action,
    get_or_create_request_id,
    request_id,
    request_ip,
    request_user_agent,
    user_id,
)
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import logger, setup_logging
from app.core.metrics import instrument_app

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Audit Service Started")
    yield
    logger.info("Audit Service Stopped")


app = FastAPI(
    title="EITOAP Audit Microservice",
    description="Security auditing, event log persistence, and compliance metrics microservice.",
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
    req_id = get_or_create_request_id(request.headers.get("x-request-id"))

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
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
instrument_app(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005, access_log=False)
