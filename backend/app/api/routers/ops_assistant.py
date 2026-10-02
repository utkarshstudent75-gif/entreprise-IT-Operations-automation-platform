import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from redis.exceptions import RedisError
from starlette.concurrency import run_in_threadpool

from app.auth.dependencies import check_role
from app.core.config import settings
from app.core.exceptions import RateLimitExceededException
from app.core.rate_limiter import rate_limiter
from app.core.redis import get_redis
from app.schemas.ops_assistant import (
    OpsAssistantAlertEvent,
    OpsAssistantChatRequest,
    OpsAssistantChatResponse,
    OpsResource,
    OpsResourceHealth,
)
from app.schemas.response import StandardResponse
from app.services.ops_assistant_service import (
    OpsAssistantNotConfigured,
    OpsAssistantUpstreamError,
    ask_ops_assistant,
    get_azure_resource_health,
    get_azure_resource_inventory,
)

logger = logging.getLogger("itpa")
ALERTS_CHANNEL = "ops-assistant:alerts:events"
ACTIVE_ALERTS_KEY = "ops-assistant:alerts:active"

ops_assistant_access = check_role(["Platform Administrator", "Support Engineer"])

router = APIRouter(
    prefix="/ops-assistant",
    tags=["AI Operations Assistant"],
    dependencies=[Depends(ops_assistant_access)],
)

alert_ingest_router = APIRouter(
    prefix="/ops-assistant/alerts",
    tags=["AI Operations Alert Ingestion"],
)


def _check_assistant_rate_limit(
    user: dict[str, Any], operation: str, limit: int
) -> None:
    try:
        rate_limiter.check_limit(
            key=f"ops-assistant:{operation}:{user['email'].lower()}",
            limit=limit,
            window_seconds=60,
        )
    except RateLimitExceededException as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many assistant requests. Please wait and try again.",
            headers={"Retry-After": "60"},
        ) from exc


@router.post("/chat", response_model=StandardResponse[OpsAssistantChatResponse])
async def chat_with_ops_assistant(
    payload: OpsAssistantChatRequest,
    current_user: dict[str, Any] = Depends(ops_assistant_access),
):
    _check_assistant_rate_limit(current_user, "chat", 20)
    answer = await ask_ops_assistant(payload.messages)
    return StandardResponse(data=OpsAssistantChatResponse(answer=answer))


@router.get(
    "/resources",
    response_model=StandardResponse[list[OpsResource]],
)
async def list_monitored_resources(
    current_user: dict[str, Any] = Depends(ops_assistant_access),
):
    _check_assistant_rate_limit(current_user, "resources", 10)
    if not settings.OPS_AZURE_SUBSCRIPTION_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure resource monitoring is not configured.",
        )
    try:
        resources = await run_in_threadpool(get_azure_resource_inventory)
    except OpsAssistantNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OpsAssistantUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return StandardResponse(data=resources)


@router.get(
    "/resource-health",
    response_model=StandardResponse[list[OpsResourceHealth]],
)
async def list_resource_health(
    current_user: dict[str, Any] = Depends(ops_assistant_access),
):
    _check_assistant_rate_limit(current_user, "resource-health", 10)
    if not settings.OPS_AZURE_SUBSCRIPTION_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure resource monitoring is not configured.",
        )
    try:
        health = await run_in_threadpool(get_azure_resource_health)
    except OpsAssistantNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OpsAssistantUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return StandardResponse(data=health)


@router.get("/alerts/stream")
async def stream_ops_alerts(
    current_user: dict[str, Any] = Depends(ops_assistant_access),
):
    _check_assistant_rate_limit(current_user, "alerts-stream", 10)
    if not settings.REDIS_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The live alert feed is not configured.",
        )
    try:
        redis = await get_redis()
        redis_connected = await redis.ping()
    except (RedisError, OSError) as exc:
        logger.error(
            "Live alert feed Redis connection failed (%s).", type(exc).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The live alert feed is temporarily unavailable.",
        ) from exc
    if not redis_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The live alert feed is temporarily unavailable.",
        )

    async def event_stream():
        pubsub = redis.pubsub()
        try:
            await pubsub.subscribe(ALERTS_CHANNEL)
            active_alerts = await redis.hvals(ACTIVE_ALERTS_KEY)
            yield _sse_message(
                "snapshot",
                {
                    "alerts": [json.loads(alert) for alert in active_alerts],
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=15.0,
                )
                if message and isinstance(message.get("data"), str):
                    yield _sse_message("alert", json.loads(message["data"]))
                else:
                    yield ": keepalive\n\n"
        except (RedisError, OSError, json.JSONDecodeError) as exc:
            logger.error("Live alert stream failed (%s).", type(exc).__name__)
        finally:
            try:
                await pubsub.unsubscribe(ALERTS_CHANNEL)
                await pubsub.aclose()
            except (RedisError, OSError) as exc:
                logger.warning(
                    "Live alert stream cleanup failed (%s).", type(exc).__name__
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_message(event_name: str, payload: dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


@alert_ingest_router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_monitor_alert(
    event: OpsAssistantAlertEvent,
    x_ops_alert_token: str | None = Header(default=None),
):
    expected_token = settings.OPS_ASSISTANT_ALERT_INGEST_TOKEN
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alert event ingestion is not configured.",
        )
    if not x_ops_alert_token or not hmac.compare_digest(
        x_ops_alert_token, expected_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Alert event authentication failed.",
        )

    try:
        redis = await get_redis()
        serialized_event = event.model_dump_json()
        if event.condition == "fired":
            await redis.hset(
                ACTIVE_ALERTS_KEY,
                event.alert.id,
                event.alert.model_dump_json(),
            )
            await redis.expire(ACTIVE_ALERTS_KEY, 7 * 24 * 60 * 60)
        else:
            await redis.hdel(ACTIVE_ALERTS_KEY, event.alert.id)
            if not await redis.hlen(ACTIVE_ALERTS_KEY):
                await redis.delete(ACTIVE_ALERTS_KEY)
        await redis.publish(ALERTS_CHANNEL, serialized_event)
    except (RedisError, OSError) as exc:
        logger.error("Alert event could not be published (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alert event delivery is temporarily unavailable.",
        ) from exc
    return {"accepted": True}
