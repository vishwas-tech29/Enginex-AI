from functools import lru_cache

from app.ai.agents.factory import build_agents
from app.ai.orchestrator import AIOrchestrator
from app.ai.providers.router import LLMRouter, build_default_router
from app.ai.rag.embeddings import HashingEmbedder
from app.ai.rag.rag_service import RAGService
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.setup import ensure_tools_registered
from app.config import settings


@lru_cache
def get_orchestrator() -> AIOrchestrator:
    router: LLMRouter = build_default_router()
    tool_registry: ToolRegistry = ensure_tools_registered()
    rag_service = RAGService(embedder=HashingEmbedder(settings.embedding_dimensions))
    agents = build_agents(router, tool_registry)
    return AIOrchestrator(
        llm_router=router, tool_registry=tool_registry, rag_service=rag_service, agents=agents
    )
