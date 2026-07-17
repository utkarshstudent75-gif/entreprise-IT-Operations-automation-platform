from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    user_id: int | None
    action: str
    status: str
    ip_address: str | None
    user_agent: str | None
    request_id: str | None
    details: dict[str, Any] | None
