from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.response import StandardResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[UserResponse],
)
async def create_user(request: UserCreate, db: Annotated[Session, Depends(get_db)]):
    user = user_service.create_user(db, request)
    return StandardResponse(data=user)
