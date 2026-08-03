import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class AIChat(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ai_chats"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)


class AIMessage(Base, UUIDPKMixin):
    __tablename__ = "ai_messages"

    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_chats.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class AIAgent(Base, UUIDPKMixin):
    __tablename__ = "ai_agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AgentMemory(Base, UUIDPKMixin):
    __tablename__ = "agent_memory"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False
    )
    chat_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_chats.id", ondelete="CASCADE"), nullable=True
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
