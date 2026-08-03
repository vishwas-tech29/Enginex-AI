import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.api.v1.ai.schemas import CreateChatRequest
from app.core.exceptions import EngineNotImplementedError, ForbiddenError, NotFoundError
from app.models.ai_chat import AIAgent, AIChat, AIMessage

SUPPORTED_PROVIDERS = ["openai", "anthropic", "gemini", "ollama", "groq", "together", "openrouter"]

_STUB_ASSISTANT_REPLY = (
    "AI response generation isn't wired to a model yet — the provider "
    "router and agent orchestration land in Phase 3 (see "
    "docs/architecture/roadmap.md). This message confirms the chat "
    "pipeline (persistence, roles, ordering) works end to end."
)


class AIService:
    def __init__(self, db: Session):
        self.db = db

    def create_chat(self, payload: CreateChatRequest, user) -> AIChat:
        chat = AIChat(project_id=payload.project_id, user_id=user.id, title=payload.title)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_chat(self, chat_id: uuid.UUID, user) -> AIChat:
        chat = self.db.get(AIChat, chat_id)
        if not chat:
            raise NotFoundError("AI chat", chat_id)
        if chat.user_id != user.id:
            raise ForbiddenError("This chat belongs to another user")
        return chat

    def delete_chat(self, chat_id: uuid.UUID, user) -> None:
        chat = self.get_chat(chat_id, user)
        self.db.delete(chat)
        self.db.commit()

    def list_messages(self, chat_id: uuid.UUID, user) -> list[AIMessage]:
        self.get_chat(chat_id, user)
        return (
            self.db.query(AIMessage)
            .filter(AIMessage.chat_id == chat_id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )

    def post_message(self, chat_id: uuid.UUID, content: str, user) -> list[AIMessage]:
        self.get_chat(chat_id, user)
        now = datetime.now(timezone.utc)

        user_message = AIMessage(chat_id=chat_id, role="user", content=content, created_at=now)
        assistant_message = AIMessage(
            chat_id=chat_id,
            role="assistant",
            content=_STUB_ASSISTANT_REPLY,
            created_at=now,
        )
        self.db.add_all([user_message, assistant_message])
        self.db.commit()
        self.db.refresh(user_message)
        self.db.refresh(assistant_message)
        return [user_message, assistant_message]

    def list_agents(self) -> list[AIAgent]:
        return self.db.query(AIAgent).all()

    def list_providers(self) -> list[dict]:
        return [{"name": name, "configured": False} for name in SUPPORTED_PROVIDERS]

    def configure_provider(self, provider: str, api_key: str) -> None:
        raise EngineNotImplementedError("provider key configuration")
