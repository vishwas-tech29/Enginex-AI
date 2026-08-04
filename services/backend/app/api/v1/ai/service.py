import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.orchestrator import AIOrchestrator, DailyCostLimitExceededError
from app.api.v1.ai.schemas import CreateChatRequest
from app.config import settings
from app.core.exceptions import EngineNotImplementedError, ForbiddenError, NotFoundError
from app.models.ai_chat import AIAgent, AIChat, AIMessage

SUPPORTED_PROVIDERS = [
    "openai",
    "anthropic",
    "gemini",
    "ollama",
    "groq",
    "together",
    "openrouter",
    "azure_openai",
]


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

    async def post_message(
        self, chat_id: uuid.UUID, content: str, user, orchestrator: AIOrchestrator, on_event=None
    ) -> list[AIMessage]:
        chat = self.get_chat(chat_id, user)
        now = datetime.now(timezone.utc)

        user_message = AIMessage(chat_id=chat_id, role="user", content=content, created_at=now)
        self.db.add(user_message)
        self.db.commit()
        self.db.refresh(user_message)

        try:
            result = await orchestrator.process_user_request(
                content, self.db, user, chat_id=chat_id, project_id=chat.project_id, on_event=on_event
            )
            assistant_content = result.response
            tool_calls = result.tool_calls
            tokens_used = result.tokens_used["input"] + result.tokens_used["output"]
            cost_usd = result.cost_usd
            model_used = ",".join(result.agents_used) or None
        except DailyCostLimitExceededError as exc:
            assistant_content, tool_calls, tokens_used, cost_usd, model_used = str(exc), [], 0, 0.0, None

        assistant_message = AIMessage(
            chat_id=chat_id,
            role="assistant",
            content=assistant_content,
            tool_calls=tool_calls,
            model_used=model_used,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(assistant_message)
        self.db.commit()
        self.db.refresh(assistant_message)
        return [user_message, assistant_message]

    def list_agents(self) -> list[AIAgent]:
        return self.db.query(AIAgent).all()

    def list_providers(self) -> list[dict]:
        configured = {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "gemini": bool(settings.gemini_api_key),
            "groq": bool(settings.groq_api_key),
            "together": bool(settings.together_api_key),
            "openrouter": bool(settings.openrouter_api_key),
            "azure_openai": bool(settings.azure_openai_api_key),
            "ollama": True,  # local server, no API key needed
        }
        return [{"name": name, "configured": configured.get(name, False)} for name in SUPPORTED_PROVIDERS]

    def configure_provider(self, provider: str, api_key: str) -> None:
        raise EngineNotImplementedError("provider key configuration")
