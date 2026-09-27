from datetime import datetime

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class SoftwareRequestCreate(BaseModel):
    software_name: str = Field(min_length=2, max_length=255)
    justification: str = Field(min_length=8, max_length=1000)

    @field_validator("software_name", "justification", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class SoftwareDecision(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class SoftwareRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    software_name: str
    justification: str = Field(
        validation_alias=AliasChoices("reason", "justification")
    )
    requester_email: EmailStr | None
    status: str
    decided_by_email: EmailStr | None
    decision_note: str | None
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None
