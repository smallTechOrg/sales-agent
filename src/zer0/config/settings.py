"""Application settings loaded from .env.

Spec: spec/product/02-architecture.md — Module responsibilities / config/
Spec: spec/engineering/secret-hygiene.md — secrets enter via env vars only

Only system-level settings live here (database URL, LLM credentials, server
config). Tenant-specific secrets (OAuth tokens, WhatsApp keys, Slack webhooks)
are stored encrypted in the database — never in .env.
"""

import logging

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_log = logging.getLogger(__name__)


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
    llm_provider: str = Field("gemini", description="LLM provider: gemini (default).")
    gemini_api_key: str = Field(..., description="Google Gemini API key. Required.")
    llm_model: str = Field("gemini-2.5-flash", description="LLM model ID.")
    llm_max_tokens: int = Field(4096, ge=256, le=16384)

    # Web search — empty string disables discovery at runtime
    tavily_api_key: str = Field("", description="Tavily search API key. Leave blank to disable discovery.")

    # JWT auth — required in production; optional while OAuth login is not yet implemented.
    # Spec: spec/product/09-api.md §Auth — every route except /health requires JWT.
    # TODO: make required (Field(...)) once Google OAuth login is implemented.
    jwt_secret: str = Field("", description="Secret key for signing JWTs. Leave blank only in local dev.")
    jwt_algorithm: str = Field("HS256")

    # Encryption key for tenant credentials at rest.
    # Spec: spec/engineering/secret-hygiene.md — credentials stored encrypted.
    # Required before any outreach run; empty disables credential encryption (dev only).
    credential_encryption_key: str = Field(
        "", description="Fernet key for encrypting tenant credentials. Required in production."
    )

    # Server
    log_level: str = Field("INFO")
    debug: bool = Field(False)
    cors_origins: str = Field("", description="Comma-separated allowed CORS origins.")

    @model_validator(mode="after")
    def _warn_missing_secrets(self) -> "Settings":
        """Emit loud warnings when production-critical secrets are absent.

        Spec: spec/engineering/secret-hygiene.md — secrets must be set in prod.
        We warn rather than raise so local dev without these keys still works.
        """
        if not self.jwt_secret:
            _log.warning(
                "ZER0_JWT_SECRET is not set. JWT authentication is disabled. "
                "Set this before exposing the API publicly."
            )
        if not self.credential_encryption_key:
            _log.warning(
                "ZER0_CREDENTIAL_ENCRYPTION_KEY is not set. "
                "Tenant credentials cannot be encrypted; outreach channels will not work. "
                "Set a Fernet key before running outreach."
            )
        return self


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings singleton. Call once at startup."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
