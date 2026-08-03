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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
