from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T

class ErrorDetails(BaseModel):
    code: str
    message: str
    request_id: str | None = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetails
