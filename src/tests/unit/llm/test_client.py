# Phase-4 gate — LLM client tests
# Spec: spec/engineering/phases.md § Phase 4
# Spec: spec/product/05-config.md — LLM configuration
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_resolved_config():
    from zer0.domain.config import (
        ApprovalMode,
        CompanySizeRange,
        DiscoveryConfig,
        ICP,
        OutreachConfig,
        OutreachTemplates,
        QualificationConfig,
        ResolvedConfig,
        RubricCriterion,
    )

    return ResolvedConfig(
        tenant_id="t1",
        campaign_id="c1",
        offering_id="o1",
        offering_name="Acme",
        value_proposition="Save time",
        pain_points=["manual work"],
        discovery_config=DiscoveryConfig(
            sources=["web"],
            query_templates=["q"],
            geography=["US"],
            volume_per_run=5,
        ),
        icp=ICP(
            target_industries=["SaaS"],
            target_roles=["CEO"],
            company_size_range=CompanySizeRange(min=10, max=500),
            geography=["US"],
            keywords=[],
            negative_keywords=[],
        ),
        qualification_config=QualificationConfig(
            rubric_criteria=[RubricCriterion(name="fit", description="d", weight=1.0)],
            score_threshold=50.0,
            disqualifying_signals=[],
        ),
        outreach_config=OutreachConfig(
            channels_enabled=["email"],
            tone="professional",
            language_default="en",
            templates=OutreachTemplates(first_touch="Hi"),
            follow_up_count=1,
            follow_up_spacing_days=3,
            send_schedule="09:00-17:00 Mon-Fri",
        ),
        approval_mode=ApprovalMode.full_auto,
    )


@pytest.fixture
def mock_genai():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "test response"
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


# ---------------------------------------------------------------------------
# complete() tests
# ---------------------------------------------------------------------------


class TestLLMClientComplete:
    def test_returns_text_from_api(self, minimal_env, mock_genai) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.providers.gemini.genai.Client", return_value=mock_genai):
            client = LLMClient(settings=Settings())
            result = client.complete(system="You are helpful", user="Say hi")

        assert result == "test response"

    def test_passes_temperature_to_api(self, minimal_env, mock_genai) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.providers.gemini.genai.Client", return_value=mock_genai):
            client = LLMClient(settings=Settings())
            client.complete(system="sys", user="usr", temperature=0.1)

        kwargs = mock_genai.models.generate_content.call_args[1]
        assert kwargs["config"].temperature == 0.1

    def test_uses_model_and_max_tokens_from_settings(
        self, minimal_env, mock_genai, monkeypatch
    ) -> None:
        monkeypatch.setenv("ZER0_LLM_MODEL", "gemini-test-model")
        monkeypatch.setenv("ZER0_LLM_MAX_TOKENS", "512")

        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.providers.gemini.genai.Client", return_value=mock_genai):
            client = LLMClient(settings=Settings())
            client.complete(system="s", user="u")

        kwargs = mock_genai.models.generate_content.call_args[1]
        assert kwargs["model"] == "gemini-test-model"
        assert kwargs["config"].max_output_tokens == 512


# ---------------------------------------------------------------------------
# load_prompt() tests
# ---------------------------------------------------------------------------


class TestLoadPrompt:
    def test_injects_config_variables_into_template(
        self, minimal_env, mock_genai, tmp_path
    ) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        (tmp_path / "greet.md").write_text("Hi {{ company_name }}, tone: {{ tone }}")

        with patch("zer0.llm.providers.gemini.genai.Client", return_value=mock_genai):
            with patch("zer0.llm.providers.gemini._PROMPTS_DIR", tmp_path):
                client = LLMClient(settings=Settings())
                result = client.load_prompt("greet", _make_resolved_config())

        assert result == "Hi Acme, tone: professional"

    def test_unknown_placeholder_left_unchanged(self, minimal_env, mock_genai, tmp_path) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        (tmp_path / "tmpl.md").write_text("Hello {{ unknown_var }}")

        with patch("zer0.llm.providers.gemini.genai.Client", return_value=mock_genai):
            with patch("zer0.llm.providers.gemini._PROMPTS_DIR", tmp_path):
                client = LLMClient(settings=Settings())
                result = client.load_prompt("tmpl", _make_resolved_config())

        assert "{{ unknown_var }}" in result

    def test_extra_kwargs_override_defaults(self, minimal_env, mock_genai, tmp_path) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        (tmp_path / "tmpl.md").write_text("{{ lead_name }}")

        with patch("zer0.llm.providers.gemini.genai.Client", return_value=mock_genai):
            with patch("zer0.llm.providers.gemini._PROMPTS_DIR", tmp_path):
                client = LLMClient(settings=Settings())
                result = client.load_prompt("tmpl", _make_resolved_config(), lead_name="Alice")

        assert result == "Alice"


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


class TestLLMFactory:
    def test_create_llm_client_default_gemini(self, minimal_env) -> None:
        from zer0.llm.providers.factory import create_llm_client
        from zer0.llm.providers.gemini import GeminiProvider

        with patch("zer0.llm.providers.gemini.genai.Client"):
            client = create_llm_client()
        assert isinstance(client, GeminiProvider)

    def test_create_llm_client_explicit_gemini(self, minimal_env) -> None:
        from zer0.llm.providers.factory import create_llm_client
        from zer0.llm.providers.gemini import GeminiProvider

        with patch("zer0.llm.providers.gemini.genai.Client"):
            client = create_llm_client(provider="gemini")
        assert isinstance(client, GeminiProvider)

    def test_create_llm_client_unsupported_provider(self, minimal_env) -> None:
        from zer0.llm.providers.factory import create_llm_client

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_client(provider="anthropic")

    def test_register_provider(self, minimal_env) -> None:
        from zer0.llm.providers.base import LLMProvider
        from zer0.llm.providers.factory import create_llm_client, register_provider

        class MockProvider(LLMProvider):
            def __init__(self, settings: object = None) -> None:
                pass

            def complete(self, *, system: str, user: str, temperature: float = 0.3) -> str:
                return "mock"

            def load_prompt(self, name: str, config: object, **extra: object) -> str:
                return "mock"

        register_provider("mock", MockProvider)
        client = create_llm_client(provider="mock")
        assert isinstance(client, MockProvider)
