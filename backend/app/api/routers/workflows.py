from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"],
)


@router.get("")
async def get_workflows(current_user: Annotated[User, Depends(get_current_user)]):
    return {"status": "coming soon"}
