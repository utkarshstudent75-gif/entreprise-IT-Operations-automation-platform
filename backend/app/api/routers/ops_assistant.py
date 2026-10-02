from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.auth.dependencies import check_role
from app.core.config import settings
from app.schemas.ops_assistant import (
    OpsAssistantChatRequest,
    OpsAssistantChatResponse,
    OpsResource,
    OpsResourceHealth,
)
from app.schemas.response import StandardResponse
from app.services.ops_assistant_service import (
    OpsAssistantUpstreamError,
    ask_ops_assistant,
    get_azure_resource_health,
    get_azure_resource_inventory,
)

router = APIRouter(
    prefix="/ops-assistant",
    tags=["AI Operations Assistant"],
    dependencies=[Depends(check_role(["Platform Administrator", "Support Engineer"]))],
)


@router.post("/chat", response_model=StandardResponse[OpsAssistantChatResponse])
async def chat_with_ops_assistant(
    payload: OpsAssistantChatRequest,
):
    answer = await ask_ops_assistant(payload.messages)
    return StandardResponse(data=OpsAssistantChatResponse(answer=answer))


@router.get(
    "/resources",
    response_model=StandardResponse[list[OpsResource]],
)
async def list_monitored_resources():
    if not settings.OPS_AZURE_SUBSCRIPTION_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure resource monitoring is not configured.",
        )
    try:
        resources = await run_in_threadpool(get_azure_resource_inventory)
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
async def list_resource_health():
    if not settings.OPS_AZURE_SUBSCRIPTION_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure resource monitoring is not configured.",
        )
    try:
        health = await run_in_threadpool(get_azure_resource_health)
    except OpsAssistantUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return StandardResponse(data=health)
