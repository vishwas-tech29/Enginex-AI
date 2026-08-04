from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    GROQ = "groq"
    TOGETHER = "together"
    OPENROUTER = "openrouter"
    AZURE_OPENAI = "azure_openai"
    FAKE = "fake"  # deterministic, no network — used in dev/tests


@dataclass
class LLMMessage:
    """Unified message format across providers."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class LLMResponse:
    """Unified response format across providers."""

    content: str
    stop_reason: str  # "end_turn", "tool_use", "stop_sequence", "length"
    tool_calls: list[dict] = field(default_factory=list)
    tokens_used: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    cost: float = 0.0
    model: str = ""
    provider: str = ""


class LLMProviderError(Exception):
    """Raised when a provider call fails — the router catches this to fall back."""


class BaseLLMProvider(ABC):
    """Base class for all LLM providers."""

    provider_type: LLMProvider

    @abstractmethod
    async def call_model(
        self,
        model: str,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Call the LLM model."""

    @abstractmethod
    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD for token usage on a given model."""
