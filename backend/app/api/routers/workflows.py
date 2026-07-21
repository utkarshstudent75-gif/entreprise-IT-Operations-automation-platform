from fastapi import APIRouter

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


@router.get("")
async def get_workflows():
    return {"status": "coming soon"}
