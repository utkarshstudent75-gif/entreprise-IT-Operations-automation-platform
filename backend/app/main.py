import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging_config import setup_logging
# Initialize logging configuration immediately on import
setup_logging()

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.context import request_ip, request_user_agent, request_id, user_id, action
from app.core.exception_handlers import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade IT Helpdesk Automation Platform",
    version=settings.APP_VERSION,
)
register_exception_handlers(app)


@app.middleware("http")
async def add_audit_context_middleware(request: Request, call_next):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None

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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

