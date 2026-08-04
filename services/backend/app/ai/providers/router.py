import logging
from typing import Awaitable, Callable

from app.ai.providers.base import BaseLLMProvider, LLMMessage, LLMProvider, LLMProviderError, LLMResponse
from app.config import settings

logger = logging.getLogger("enginex.ai.router")

UsageCallback = Callable[[LLMProvider, LLMResponse], Awaitable[None]]


class AllProvidersFailedError(Exception):
    def __init__(self, attempts: list[tuple[LLMProvider, str]]):
        self.attempts = attempts
        detail = "; ".join(f"{p.value}: {err}" for p, err in attempts)
        super().__init__(f"All LLM providers failed — {detail}" if attempts else "No LLM providers configured")


class LLMRouter:
    """Routes model calls to configured providers with automatic fallback."""

    def __init__(self, primary: LLMProvider | None = None, fallback_chain: list[LLMProvider] | None = None):
        self.providers: dict[LLMProvider, BaseLLMProvider] = {}
        self.primary_provider = primary
        self.fallback_chain = fallback_chain or []
        self._usage_callback: UsageCallback | None = None

    def register_provider(self, provider: BaseLLMProvider) -> None:
        self.providers[provider.provider_type] = provider

    def on_usage(self, callback: UsageCallback) -> None:
        self._usage_callback = callback

    def _provider_chain(self, preferred: LLMProvider | None) -> list[LLMProvider]:
        chain: list[LLMProvider] = []
        for candidate in [preferred, self.primary_provider, *self.fallback_chain]:
            if candidate is not None and candidate not in chain:
                chain.append(candidate)
        return chain

    async def call_model(
        self,
        model: str,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        preferred_provider: LLMProvider | None = None,
    ) -> LLMResponse:
        attempts: list[tuple[LLMProvider, str]] = []

        for provider_type in self._provider_chain(preferred_provider):
            provider = self.providers.get(provider_type)
            if provider is None:
                continue

            try:
                logger.info("ai_provider_call", extra={"provider": provider_type.value, "model": model})
                response = await provider.call_model(
                    model=model, messages=messages, tools=tools, temperature=temperature, max_tokens=max_tokens
                )
            except LLMProviderError as exc:
                logger.warning("ai_provider_failed", extra={"provider": provider_type.value, "error": str(exc)})
                attempts.append((provider_type, str(exc)))
                continue

            if self._usage_callback:
                await self._usage_callback(provider_type, response)
            return response

        raise AllProvidersFailedError(attempts)


def build_default_router() -> LLMRouter:
    """Wire up a router from whichever provider API keys are configured."""
    from app.ai.providers.anthropic_provider import AnthropicProvider
    from app.ai.providers.fake_provider import FakeProvider
    from app.ai.providers.gemini_provider import GeminiProvider
    from app.ai.providers.openai_compatible import OpenAICompatibleProvider

    try:
        primary = LLMProvider(settings.ai_primary_provider)
    except ValueError:
        primary = LLMProvider.FAKE
    fallback_chain = [
        p for p in (_safe_provider(name) for name in settings.ai_fallback_providers_list) if p is not None
    ]

    router = LLMRouter(primary=primary, fallback_chain=fallback_chain)

    if settings.anthropic_api_key:
        router.register_provider(AnthropicProvider(api_key=settings.anthropic_api_key))
    if settings.openai_api_key:
        router.register_provider(OpenAICompatibleProvider(LLMProvider.OPENAI, api_key=settings.openai_api_key))
    if settings.gemini_api_key:
        router.register_provider(GeminiProvider(api_key=settings.gemini_api_key))
    if settings.groq_api_key:
        router.register_provider(
            OpenAICompatibleProvider(
                LLMProvider.GROQ, api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1"
            )
        )
    if settings.together_api_key:
        router.register_provider(
            OpenAICompatibleProvider(
                LLMProvider.TOGETHER,
                api_key=settings.together_api_key,
                base_url="https://api.together.xyz/v1",
            )
        )
    if settings.openrouter_api_key:
        router.register_provider(
            OpenAICompatibleProvider(
                LLMProvider.OPENROUTER,
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        )
    if settings.azure_openai_api_key and settings.azure_openai_endpoint:
        router.register_provider(
            OpenAICompatibleProvider(
                LLMProvider.AZURE_OPENAI,
                api_key=settings.azure_openai_api_key,
                base_url=settings.azure_openai_endpoint,
            )
        )
    # Ollama needs no API key — it's a local server; register only if a
    # caller actually wants to use it (avoids probing localhost every boot).

    # The fake provider is always available as the last-resort fallback so
    # the system degrades gracefully instead of hard-failing when no real
    # provider is configured (e.g. local dev without API keys).
    router.register_provider(FakeProvider())
    if LLMProvider.FAKE not in router.fallback_chain:
        router.fallback_chain.append(LLMProvider.FAKE)

    return router


def _safe_provider(name: str) -> LLMProvider | None:
    try:
        return LLMProvider(name)
    except ValueError:
        return None
