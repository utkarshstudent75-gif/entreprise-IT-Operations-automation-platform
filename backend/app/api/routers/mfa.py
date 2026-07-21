from fastapi import APIRouter

router = APIRouter(
    prefix="/mfa",
    tags=["MFA"],
)


@router.get("")
async def get_mfa():
    return {"status": "coming soon"}


@router.post("")
async def create_mfa_request():
    return {"status": "coming soon"}
