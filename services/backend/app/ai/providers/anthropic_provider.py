from anthropic import AsyncAnthropic

from app.ai.providers.base import BaseLLMProvider, LLMMessage, LLMProvider, LLMProviderError, LLMResponse

PRICING = {
    "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-latest": {"input": 0.0008, "output": 0.004},
    "claude-3-opus-latest": {"input": 0.015, "output": 0.075},
}
DEFAULT_PRICING = {"input": 0.003, "output": 0.015}


class AnthropicProvider(BaseLLMProvider):
    provider_type = LLMProvider.ANTHROPIC

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def call_model(
        self,
        model: str,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        system_prompt = "\n".join(m.content for m in messages if m.role == "system")
        conversation = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": conversation,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = tools  # already Anthropic-shaped: {name, description, input_schema}

        try:
            response = await self.client.messages.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"anthropic call failed: {exc}") from exc

        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({"name": block.name, "arguments": block.input})

        tokens_input = response.usage.input_tokens
        tokens_output = response.usage.output_tokens

        return LLMResponse(
            content=content,
            stop_reason=response.stop_reason or "end_turn",
            tool_calls=tool_calls,
            tokens_used={"input": tokens_input, "output": tokens_output},
            cost=self.calculate_cost(model, tokens_input, tokens_output),
            model=model,
            provider=self.provider_type.value,
        )

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        rates = PRICING.get(model, DEFAULT_PRICING)
        return (tokens_input / 1000) * rates["input"] + (tokens_output / 1000) * rates["output"]
