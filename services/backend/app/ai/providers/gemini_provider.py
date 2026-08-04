from google import genai
from google.genai import types

from app.ai.providers.base import BaseLLMProvider, LLMMessage, LLMProvider, LLMProviderError, LLMResponse

PRICING = {
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
}
DEFAULT_PRICING = {"input": 0.000075, "output": 0.0003}

_ROLE_MAP = {"assistant": "model", "user": "user"}


class GeminiProvider(BaseLLMProvider):
    provider_type = LLMProvider.GEMINI

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def call_model(
        self,
        model: str,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        system_instruction = "\n".join(m.content for m in messages if m.role == "system") or None
        contents = [
            types.Content(role=_ROLE_MAP.get(m.role, "user"), parts=[types.Part(text=m.content)])
            for m in messages
            if m.role != "system"
        ]

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )
        if tools:
            config.tools = [
                types.Tool(
                    function_declarations=[
                        {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                        }
                        for tool in tools
                    ]
                )
            ]

        try:
            response = await self.client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"gemini call failed: {exc}") from exc

        content = response.text or ""
        tool_calls = [
            {"name": fc.name, "arguments": dict(fc.args or {})} for fc in (response.function_calls or [])
        ]

        usage = response.usage_metadata
        tokens_input = usage.prompt_token_count if usage else 0
        tokens_output = usage.candidates_token_count if usage else 0

        finish_reason = "tool_use" if tool_calls else "end_turn"
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason = str(response.candidates[0].finish_reason)

        return LLMResponse(
            content=content,
            stop_reason=finish_reason,
            tool_calls=tool_calls,
            tokens_used={"input": tokens_input or 0, "output": tokens_output or 0},
            cost=self.calculate_cost(model, tokens_input or 0, tokens_output or 0),
            model=model,
            provider=self.provider_type.value,
        )

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        rates = PRICING.get(model, DEFAULT_PRICING)
        return (tokens_input / 1000) * rates["input"] + (tokens_output / 1000) * rates["output"]
