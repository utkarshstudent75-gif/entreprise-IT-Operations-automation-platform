from fastapi import APIRouter, Response

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


@router.get("")
async def get_metrics():
    return Response(content="", media_type="text/plain")
