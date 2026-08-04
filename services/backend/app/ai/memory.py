import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_chat import AgentMemory, AIMessage


class MemorySystem:
    """Conversation + shared long-term memory for agents.

    Short-term (current conversation) is just the AIMessage history for a
    chat — already persisted by AIService (see app/api/v1/ai/service.py).
    Long-term is `AgentMemory` rows scoped to a chat/project: durable facts
    ("target voltage: 5V", "preferred MCU: STM32F1") any agent working that
    chat can read or write, with optional expiry. This is project-scoped
    memory, not full cross-session user-profile learning — a real
    preference-inference pipeline is future work.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_recent_messages(self, chat_id: uuid.UUID, limit: int = 20) -> list[AIMessage]:
        return (
            self.db.query(AIMessage)
            .filter(AIMessage.chat_id == chat_id)
            .order_by(AIMessage.created_at.desc())
            .limit(limit)
            .all()[::-1]
        )

    def get_chat_memory(self, chat_id: uuid.UUID) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        rows = self.db.query(AgentMemory).filter(AgentMemory.chat_id == chat_id).all()
        return {
            row.key: row.value
            for row in rows
            if row.expires_at is None or row.expires_at.replace(tzinfo=timezone.utc) > now
        }

    def set_chat_memory(
        self,
        chat_id: uuid.UUID,
        agent_id: uuid.UUID,
        key: str,
        value: Any,
        expires_at: datetime | None = None,
    ) -> AgentMemory:
        existing = (
            self.db.query(AgentMemory)
            .filter(AgentMemory.chat_id == chat_id, AgentMemory.key == key)
            .first()
        )
        if existing:
            existing.value = value
            existing.expires_at = expires_at
            self.db.commit()
            return existing

        row = AgentMemory(agent_id=agent_id, chat_id=chat_id, key=key, value=value, expires_at=expires_at)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = self.db.query(AgentMemory).filter(AgentMemory.expires_at.isnot(None)).all()
        count = 0
        for row in expired:
            if row.expires_at and row.expires_at.replace(tzinfo=timezone.utc) <= now:
                self.db.delete(row)
                count += 1
        if count:
            self.db.commit()
        return count
