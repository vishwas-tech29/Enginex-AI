import json

from openai import AsyncOpenAI

from app.ai.providers.base import BaseLLMProvider, LLMMessage, LLMProvider, LLMProviderError, LLMResponse

# USD per 1K tokens. Approximate, illustrative — real pricing should be
# refreshed from each provider's pricing page periodically.
PRICING: dict[LLMProvider, dict[str, dict[str, float]]] = {
    LLMProvider.OPENAI: {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    },
    LLMProvider.GROQ: {
        "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
        "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
    },
    LLMProvider.TOGETHER: {
        "meta-llama/Llama-3.3-70B-Instruct-Turbo": {"input": 0.00088, "output": 0.00088},
    },
    LLMProvider.OPENROUTER: {
        "default": {"input": 0.001, "output": 0.002},
    },
    LLMProvider.AZURE_OPENAI: {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
    },
    LLMProvider.OLLAMA: {
        "default": {"input": 0.0, "output": 0.0},
    },
}


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for any OpenAI-Chat-Completions-shaped API.

    Covers OpenAI, Groq, Together AI, OpenRouter, Azure OpenAI, and Ollama —
    they all speak (a compatible subset of) the same wire format, so one
    implementation with a swappable base_url/api_key covers all six rather
    than duplicating near-identical client code per provider.
    """

    def __init__(self, provider_type: LLMProvider, api_key: str, base_url: str | None = None):
        self.provider_type = provider_type
        self.client = AsyncOpenAI(api_key=api_key or "not-needed", base_url=base_url)

    async def call_model(
        self,
        model: str,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        openai_messages = [{"role": m.role, "content": m.content} for m in messages]

        kwargs: dict = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            # Generic tool defs are Anthropic-shaped ({name, description,
            # input_schema}) — adapt to OpenAI's {type, function} envelope.
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                    },
                }
                for tool in tools
            ]

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001 — normalize all provider errors
            raise LLMProviderError(f"{self.provider_type.value} call failed: {exc}") from exc

        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = [
            {"name": tc.function.name, "arguments": json.loads(tc.function.arguments)}
            for tc in (choice.message.tool_calls or [])
        ]

        tokens_input = response.usage.prompt_tokens if response.usage else 0
        tokens_output = response.usage.completion_tokens if response.usage else 0

        return LLMResponse(
            content=content,
            stop_reason=choice.finish_reason or "end_turn",
            tool_calls=tool_calls,
            tokens_used={"input": tokens_input, "output": tokens_output},
            cost=self.calculate_cost(model, tokens_input, tokens_output),
            model=model,
            provider=self.provider_type.value,
        )

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        table = PRICING.get(self.provider_type, {})
        rates = table.get(model, table.get("default", {"input": 0.0, "output": 0.0}))
        return (tokens_input / 1000) * rates["input"] + (tokens_output / 1000) * rates["output"]
