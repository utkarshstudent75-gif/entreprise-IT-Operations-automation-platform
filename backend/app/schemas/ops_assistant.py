from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OpsAssistantMessage(BaseModel):
    role: Literal["user"]
    content: str = Field(min_length=1, max_length=4000)


class OpsAssistantChatRequest(BaseModel):
    messages: list[OpsAssistantMessage] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_conversation(self):
        if sum(len(message.content) for message in self.messages) > 12000:
            raise ValueError("Conversation content exceeds the maximum length.")
        return self


class OpsAssistantChatResponse(BaseModel):
    answer: str


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
