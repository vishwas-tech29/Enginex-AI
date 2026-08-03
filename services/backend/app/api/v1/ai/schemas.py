import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    project_id: uuid.UUID | None = None
    title: str = Field(default="New chat", min_length=1, max_length=255)


class ChatOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class MessageOut(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    role: str
    content: str
    tool_calls: list
    model_used: str | None
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentOut(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    prompt: str
    tools: list
    memory_enabled: bool

    model_config = {"from_attributes": True}


class ProviderOut(BaseModel):
    name: str
    configured: bool
