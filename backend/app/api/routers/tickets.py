from fastapi import APIRouter

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.get("")
async def get_tickets():
    return {"status": "coming soon"}
