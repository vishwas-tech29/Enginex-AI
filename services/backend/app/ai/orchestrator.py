import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from sqlalchemy.orm import Session

from app.ai.agents.base_agent import BaseAgent
from app.ai.memory import MemorySystem
from app.ai.providers.base import LLMMessage, LLMResponse
from app.ai.providers.router import LLMRouter
from app.ai.rag.rag_service import RAGService
from app.ai.tools.context import ToolContext
from app.ai.tools.registry import ToolRegistry
from app.ai.usage import UsageAnalytics
from app.config import settings
from app.models.user import User

logger = logging.getLogger("enginex.ai.orchestrator")

INTENT_TO_AGENT = {
    "mechanical_design": "mechanical_cad",
    "pcb_design": "pcb_design",
    "electronics": "electronics",
    "simulation": "simulation",
    "firmware": "firmware",
    "manufacturing": "manufacturing",
    "documentation": "documentation",
    "component_recommendation": "component_recommendation",
    "general": "planner",
}


class DailyCostLimitExceededError(Exception):
    pass


@dataclass
class OrchestratorResult:
    response: str
    agents_used: list[str]
    tokens_used: dict[str, int]
    cost_usd: float
    tool_calls: list[dict] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)


def _add_tokens(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    return {"input": a["input"] + b.get("input", 0), "output": a["output"] + b.get("output", 0)}


class AIOrchestrator:
    """Classifies intent, retrieves RAG context, dispatches to the matching
    specialist agent(s), and synthesizes a single response.

    Routing is intent-classification-driven rather than a free-text
    plan-parser: the LLM names 1-2 categories from a fixed list, which map
    deterministically to agent keys. A free-text "planner writes a plan,
    orchestrator regexes it apart" design is exactly the kind of thing that
    silently breaks when the model phrases things slightly differently —
    this is bounded, cheap to test, and doesn't need parsing.
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        tool_registry: ToolRegistry,
        rag_service: RAGService,
        agents: dict[str, BaseAgent],
    ):
        self.llm_router = llm_router
        self.tool_registry = tool_registry
        self.rag_service = rag_service
        self.agents = agents

    async def classify_intents(self, request: str) -> tuple[list[str], LLMResponse, dict, float]:
        categories = ", ".join(INTENT_TO_AGENT)
        prompt = (
            f"Classify this engineering request into 1-2 categories from: {categories}.\n"
            "Respond with only a comma-separated list of category names, most relevant first.\n\n"
            f"Request: {request}"
        )
        response = await self.llm_router.call_model(
            model=settings.ai_classifier_model,
            messages=[LLMMessage(role="user", content=prompt)],
            temperature=0.1,
            max_tokens=50,
        )
        candidates = [c.strip().lower() for c in response.content.split(",")]
        intents = [c for c in candidates if c in INTENT_TO_AGENT][:2] or ["general"]
        return intents, response, response.tokens_used, response.cost

    async def process_user_request(
        self,
        request: str,
        db: Session,
        user: User,
        chat_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        on_event: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> OrchestratorResult:
        usage = UsageAnalytics(db)
        memory = MemorySystem(db)

        async def emit(event_type: str, **fields) -> None:
            if on_event is not None:
                await on_event({"type": event_type, **fields})

        today_cost = usage.get_today_cost(user)
        if today_cost >= settings.ai_max_daily_cost_usd:
            raise DailyCostLimitExceededError(
                f"Daily AI spend limit reached (${today_cost:.2f} >= "
                f"${settings.ai_max_daily_cost_usd:.2f}). Try again tomorrow."
            )

        total_tokens = {"input": 0, "output": 0}
        total_cost = 0.0

        await emit("thinking", content="Classifying request…")
        intents, classify_response, classify_tokens, classify_cost = await self.classify_intents(request)
        total_tokens = _add_tokens(total_tokens, classify_tokens)
        total_cost += classify_cost
        usage.log_llm_call(
            user, "classify_intent", classify_response.provider,
            settings.ai_classifier_model, classify_tokens["input"], classify_tokens["output"], classify_cost,
            project_id,
        )
        await emit("intent_classified", intents=intents)

        rag_context: dict = {}
        try:
            rag_context = await self.rag_service.search_all_collections(request, limit=2)
        except Exception as exc:  # noqa: BLE001 — RAG is best-effort context, never fatal
            logger.warning("rag_search_failed", extra={"error": str(exc)})

        chat_memory = memory.get_chat_memory(chat_id) if chat_id else {}
        tool_ctx = ToolContext(db=db, user=user)
        context = {
            "rag_context": rag_context,
            "chat_memory": chat_memory,
            "project_id": str(project_id) if project_id else None,
            "_tool_ctx": tool_ctx,
            "_on_event": on_event,
        }

        agents_used: list[str] = []
        tool_calls: list[dict] = []
        response_parts: list[str] = []

        for intent in intents:
            agent_key = INTENT_TO_AGENT.get(intent, "planner")
            agent = self.agents.get(agent_key)
            if agent is None:
                continue

            state = await agent.run(request, context)
            agents_used.append(agent_key)
            tool_calls.extend(state["tools_used"])
            response_parts.append(state["result"])
            total_tokens = _add_tokens(total_tokens, state["tokens_used"])
            total_cost += state["cost"]
            usage.log_llm_call(
                user, f"agent:{agent_key}", "router", agent.model,
                state["tokens_used"]["input"], state["tokens_used"]["output"], state["cost"], project_id,
            )

        if not response_parts:
            final_response = "I couldn't determine how to help with that request."
        elif len(response_parts) == 1:
            final_response = response_parts[0]
        else:
            final_response, synthesis_cost = await self._synthesize(
                request, agents_used, response_parts, total_tokens, user, usage, project_id
            )
            total_cost += synthesis_cost

        return OrchestratorResult(
            response=final_response,
            agents_used=agents_used,
            tokens_used=total_tokens,
            cost_usd=total_cost,
            tool_calls=tool_calls,
            intents=intents,
        )

    async def _synthesize(
        self, request, agents_used, response_parts, total_tokens, user, usage, project_id
    ) -> tuple[str, float]:
        joined = "\n\n".join(f"[{agent}]: {part}" for agent, part in zip(agents_used, response_parts))
        prompt = (
            f"Original request: {request}\n\nSpecialist results:\n{joined}\n\n"
            "Combine these into one clear, coherent response for the user."
        )
        response = await self.llm_router.call_model(
            model=settings.ai_default_model,
            messages=[LLMMessage(role="user", content=prompt)],
            temperature=0.4,
        )
        total_tokens["input"] += response.tokens_used.get("input", 0)
        total_tokens["output"] += response.tokens_used.get("output", 0)
        usage.log_llm_call(
            user, "synthesize", response.provider, response.model,
            response.tokens_used.get("input", 0), response.tokens_used.get("output", 0), response.cost, project_id,
        )
        return response.content, response.cost
