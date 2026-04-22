# Phase-2 gate (settings) — per spec/engineering/phases.md
from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.conftest import MINIMAL_ENV


class TestSettings:
    def test_reads_required_fields_from_env(self, minimal_env) -> None:
        from zer0.config.settings import Settings

        s = Settings()
        assert s.database_url == MINIMAL_ENV["ZER0_DATABASE_URL"]
        assert s.gemini_api_key == MINIMAL_ENV["ZER0_GEMINI_API_KEY"]
        assert s.tavily_api_key == MINIMAL_ENV["ZER0_TAVILY_API_KEY"]

    def test_default_values_are_applied(self, minimal_env) -> None:
        from zer0.config.settings import Settings

        s = Settings()
        assert s.llm_provider == "gemini"
        assert s.llm_model == "gemini-2.5-flash"
        assert s.llm_max_tokens == 4096
        assert s.log_level == "INFO"
        assert s.debug is False
        assert s.jwt_algorithm == "HS256"


    def test_missing_gemini_key_raises_validation_error(self, monkeypatch) -> None:
        for k, v in MINIMAL_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.delenv("ZER0_GEMINI_API_KEY", raising=False)

        from zer0.config.settings import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_get_settings_returns_singleton(self, minimal_env) -> None:
        import zer0.config.settings as _s

        s1 = _s.get_settings()
        s2 = _s.get_settings()
        assert s1 is s2

    def test_llm_max_tokens_below_minimum_raises(self, monkeypatch) -> None:
        for k, v in MINIMAL_ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("ZER0_LLM_MAX_TOKENS", "100")  # below ge=256

        from zer0.config.settings import Settings

        with pytest.raises(ValidationError):
            Settings()
