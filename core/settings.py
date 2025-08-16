from __future__ import annotations
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, typed configuration loaded from env or .env.local."""

    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8", extra="ignore")

    ENV: str = Field(default="dev")
    LOG_LEVEL: str = Field(default="INFO")

    # Bus
    BUS_BASE_URL: str = Field(default="http://127.0.0.1:8081")
    BUS_TOKEN: str | None = None

    # Agent security
    AGENT_SHARED_SECRET: str | None = None

    # Model backends
    OLLAMA_URL: str = Field(default="http://127.0.0.1:11434")
    OPENAI_API_KEY: str | None = None

    # Google integrations (optional)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None


def require_secret(name: str, value: str | None) -> None:
    if not value:
        raise RuntimeError(f"Missing required secret: {name}. Set it in env or .env.local")


settings = Settings()
