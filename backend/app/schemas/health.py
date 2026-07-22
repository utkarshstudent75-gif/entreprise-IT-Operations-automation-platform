from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    redis: str
    application: str = "healthy"
    sms_provider: str = "connected"


class LiveResponse(BaseModel):
    status: str
