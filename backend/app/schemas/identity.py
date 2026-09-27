from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AccountUnlockRequestCreate(BaseModel):
    email: EmailStr
    justification: str = Field(min_length=8, max_length=1000)

    @field_validator("justification", mode="before")
    @classmethod
    def strip_justification(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class AccountUnlockRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_email: EmailStr
    justification: str
    status: str
    created_at: datetime


class MFAResetRequest(BaseModel):
    email: EmailStr


class MFAResetResult(BaseModel):
    message: str
    methods_removed: int
