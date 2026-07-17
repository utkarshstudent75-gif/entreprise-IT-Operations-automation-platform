from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    database: str


class LiveResponse(BaseModel):
    status: str
