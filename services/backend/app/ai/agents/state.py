from typing import Any, TypedDict

from app.ai.providers.base import LLMMessage


class AgentState(TypedDict):
    task: str
    context: dict[str, Any]
    messages: list[LLMMessage]
    tools_used: list[dict[str, Any]]
    reasoning: str
    result: str
    tokens_used: dict[str, int]
    cost: float
