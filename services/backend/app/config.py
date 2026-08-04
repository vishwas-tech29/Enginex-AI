from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Enginex AI API"
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+psycopg2://postgres:password@localhost:5432/enginex"

    # Redis / RabbitMQ
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672"

    # Object storage
    storage_backend: str = "local"  # "local" or "s3"
    storage_root: str = "./storage"
    max_upload_size_bytes: int = 100 * 1024 * 1024

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "enginex-files"
    s3_region: str = "us-east-1"

    # Auth
    jwt_secret: str = "change-me-in-local-env-only"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000"

    # AI providers — all optional. Unset providers are simply unavailable to
    # the router; nothing crashes at startup without keys configured.
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    together_api_key: str | None = None
    openrouter_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    ollama_base_url: str = "http://localhost:11434/v1"

    ai_primary_provider: str = "anthropic"
    ai_fallback_providers: str = "openai,gemini"
    ai_default_model: str = "claude-3-5-sonnet-latest"
    ai_classifier_model: str = "claude-3-5-haiku-latest"
    ai_max_daily_cost_usd: float = 10.0

    # RAG / vector store. ":memory:" needs no running Qdrant server — good
    # for dev/test; point at a real URL (see docker-compose.yml) in prod.
    qdrant_url: str = ":memory:"
    embedding_dimensions: int = 256

    # Landing page / billing. Public-facing URLs the landing app and emails
    # link back into; frontend_url is the Next.js app, landing_url is the
    # standalone Velorah marketing site (apps/velorah).
    frontend_url: str = "http://localhost:3000"
    landing_url: str = "http://localhost:5173"

    # Stripe — optional, like the AI provider keys above. Billing endpoints
    # return a clean 503 rather than crashing when these are unset.
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_hobbyist_monthly: str | None = None
    stripe_price_hobbyist_annual: str | None = None
    stripe_price_professional_monthly: str | None = None
    stripe_price_professional_annual: str | None = None

    # Email — optional SMTP. Unset means EmailService logs instead of
    # sending, so signup/dev flows never hard-fail on a missing mail server.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_email: str = "noreply@velorah.io"
    smtp_from_name: str = "Velorah"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_fallback_providers_list(self) -> list[str]:
        return [p.strip() for p in self.ai_fallback_providers.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
