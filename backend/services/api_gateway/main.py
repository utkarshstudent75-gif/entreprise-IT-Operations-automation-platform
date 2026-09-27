# ruff: noqa: E402
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
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
from app.core.redis import redis_manager

setup_logging()

# Configurable Service URLs for Microservices Routing
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
TICKET_SERVICE_URL = os.getenv("TICKET_SERVICE_URL", "http://127.0.0.1:8002")
WORKFLOW_SERVICE_URL = os.getenv("WORKFLOW_SERVICE_URL", "http://127.0.0.1:8003")
NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL", "http://127.0.0.1:8004"
)
AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://127.0.0.1:8005")

ENABLE_REVERSE_PROXY = os.getenv("ENABLE_REVERSE_PROXY", "false").lower() == "true"

client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    redis_manager.init_redis()
    if await redis_manager.ping():
        logger.info("API Gateway: Redis Connected")
    else:
        logger.error("API Gateway: Redis Connection Failed")

    client = httpx.AsyncClient(timeout=10.0)
    yield
    await client.aclose()
    await redis_manager.close()


app = FastAPI(
    title=settings.APP_NAME + " - API Gateway",
    description="Central API Gateway for Enterprise IT Operations Automation Platform microservices.",
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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)

# Mount local API router for in-process monolithic mode / test fallback
app.include_router(api_router, prefix="/api/v1")
instrument_app(app)


def get_target_service_url(path: str) -> str | None:
    """Map incoming request path to target microservice URL."""
    if (
        path.startswith("/api/v1/users")
        or path.startswith("/api/v1/password")
        or path.startswith("/api/v1/mfa")
    ):
        return AUTH_SERVICE_URL
    if path.startswith("/api/v1/tickets"):
        return TICKET_SERVICE_URL
    if path.startswith("/api/v1/workflows") or path.startswith("/api/v1/software"):
        return WORKFLOW_SERVICE_URL
    if path.startswith("/api/v1/notifications"):
        return NOTIFICATION_SERVICE_URL
    if (
        path.startswith("/api/v1/audit-logs")
        or path.startswith("/api/v1/dashboard")
        or path.startswith("/api/v1/metrics")
    ):
        return AUDIT_SERVICE_URL
    return None


@app.api_route(
    "/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy_request(request: Request, path: str):
    """Reverse proxy router dispatching requests to microservices."""
    full_path = f"/api/v1/{path}"
    target_host = get_target_service_url(full_path)
    if not target_host or not client:
        return JSONResponse(
            status_code=404, content={"error": "Target microservice route not found"}
        )

    url = f"{target_host}{full_path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    if correlation_id := request_id.get():
        headers["x-request-id"] = correlation_id

    body = await request.body()
    try:
        req = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body,
        )
        res = await client.send(req)
        return Response(
            content=res.content, status_code=res.status_code, headers=dict(res.headers)
        )
    except httpx.RequestError as exc:
        logger.error(
            "Gateway failed to reach downstream service (%s).", type(exc).__name__
        )
        return JSONResponse(
            status_code=503, content={"error": "Downstream microservice unavailable"}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
