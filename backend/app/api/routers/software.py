from fastapi import APIRouter

router = APIRouter(
    prefix="/software",
    tags=["Software Requests"],
)


@router.get("")
async def get_software():
    return {"status": "coming soon"}


@router.post("")
async def create_software_request():
    return {"status": "coming soon"}
