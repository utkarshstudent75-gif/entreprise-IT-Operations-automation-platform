from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    redis: str


class LiveResponse(BaseModel):
    status: str
