# ruff: noqa: E402
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
from app.schemas.response import StandardResponse
from app.services.notification_service import notification_service

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification Service Started")
    yield
    logger.info("Notification Service Stopped")


app = FastAPI(
    title="EITOAP Notification Microservice",
    description="SMS, email, and alert dispatch microservice.",
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


class SMSDispatchPayload(BaseModel):
    phone_number: str
    message: str


router = APIRouter(prefix="/notifications", tags=["Notifications"])


from app.schemas.sms import SmsRequest


@router.post("/send-sms", status_code=status.HTTP_200_OK)
async def send_sms(payload: SMSDispatchPayload):
    req = SmsRequest(phone_number=payload.phone_number, message=payload.message)
    sent = notification_service.send_sms(req)
    return StandardResponse(data={"success": sent})


app.include_router(health_router)
app.include_router(router, prefix="/api/v1")
instrument_app(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004, access_log=False)
