from collections import deque

from app.ai.providers.base import BaseLLMProvider, LLMMessage, LLMProvider, LLMResponse


class FakeProvider(BaseLLMProvider):
    """Deterministic, no-network provider for dev and tests.

    Used as the default when no real provider API key is configured, and
    directly by tests that need predictable orchestrator behavior without
    hitting a real LLM. Queue canned responses via `enqueue()`; falls back
    to a simple deterministic echo when the queue is empty.
    """

    provider_type = LLMProvider.FAKE

    def __init__(self) -> None:
        self._queue: deque[LLMResponse] = deque()

    def enqueue(self, response: LLMResponse) -> None:
        self._queue.append(response)

    def enqueue_text(self, content: str, stop_reason: str = "end_turn", tool_calls: list[dict] | None = None) -> None:
        self.enqueue(
            LLMResponse(
                content=content,
                stop_reason=stop_reason,
                tool_calls=tool_calls or [],
                tokens_used={"input": max(len(content) // 4, 1), "output": max(len(content) // 4, 1)},
                cost=0.0,
                provider=self.provider_type.value,
            )
        )

    async def call_model(
        self,
        model: str,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if self._queue:
            response = self._queue.popleft()
            response.model = model
            return response

        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        content = f"[fake:{model}] acknowledged: {last_user[:200]}"
        return LLMResponse(
            content=content,
            stop_reason="end_turn",
            tool_calls=[],
            tokens_used={"input": max(len(last_user) // 4, 1), "output": max(len(content) // 4, 1)},
            cost=0.0,
            model=model,
            provider=self.provider_type.value,
        )

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        return 0.0
