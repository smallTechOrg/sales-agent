"""Application settings loaded from .env.

Spec: spec/product/02-architecture.md — Module responsibilities / config/
Spec: spec/engineering/secret-hygiene.md — secrets enter via env vars only

Only system-level settings live here (database URL, LLM credentials, server
config). Tenant-specific secrets (OAuth tokens, WhatsApp keys, Slack webhooks)
are stored encrypted in the database — never in .env.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ZER0_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(..., description="Postgres connection URL. Required.")

    # LLM
    anthropic_api_key: str = Field(..., description="Anthropic API key. Required.")
    llm_model: str = Field("claude-sonnet-4-6", description="Anthropic model ID.")
    llm_max_tokens: int = Field(4096, ge=256, le=16384)

    # Web search
    tavily_api_key: str = Field(..., description="Tavily search API key. Required.")

    # JWT auth
    jwt_secret: str = Field(..., description="Secret key for signing JWTs. Required.")
    jwt_algorithm: str = Field("HS256")

    # Encryption key for tenant credentials at rest
    credential_encryption_key: str = Field(
        ..., description="Fernet key for encrypting tenant credentials. Required."
    )

    # Server
    log_level: str = Field("INFO")
    debug: bool = Field(False)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings singleton. Call once at startup."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
