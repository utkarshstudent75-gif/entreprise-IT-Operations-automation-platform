from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OpsAssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class OpsAssistantChatRequest(BaseModel):
    messages: list[OpsAssistantMessage] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_conversation(self):
        if any(
            message.role == "user" and len(message.content) > 4000
            for message in self.messages
        ):
            raise ValueError("User messages exceed the maximum length.")
        if sum(len(message.content) for message in self.messages) > 12000:
            raise ValueError("Conversation content exceeds the maximum length.")
        if self.messages[-1].role != "user":
            raise ValueError("The latest conversation message must be from the user.")
        return self


class OpsAssistantChatResponse(BaseModel):
    answer: str


class OpsAssistantAlert(BaseModel):
    id: str = Field(min_length=1, max_length=512)
    source: Literal[
        "Azure Monitor",
        "Azure Resource Health",
        "Azure Activity",
        "Azure Diagnostics",
        "AKS events",
        "AKS container logs",
    ]
    severity: Literal["warning", "error", "critical"]
    title: str = Field(min_length=1, max_length=160)
    resource_name: str | None = Field(default=None, max_length=256)
    scope: str | None = Field(default=None, max_length=256)
    occurred_at: str | None = Field(default=None, max_length=80)
    summary: str = Field(min_length=1, max_length=2048)


class OpsAssistantAlertEvent(BaseModel):
    condition: Literal["fired", "resolved"]
    alert: OpsAssistantAlert


class OpsAssistantAlertsResponse(BaseModel):
    checked_at: str
    alerts: list[OpsAssistantAlert]
    unavailable_sources: list[str]


class OpsResource(BaseModel):
    id: str
    name: str
    type: str
    resource_group: str
    location: str | None = None


class OpsResourceHealth(BaseModel):
    name: str
    type: str
    resource_group: str
    availability_state: str
    reason_type: str | None = None
