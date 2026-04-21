# Phase-4 gate — LLM client tests
# Spec: spec/engineering/phases.md § Phase 4
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
def mock_anthropic_cls():
    mock_cls = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="test response")]
    mock_cls.return_value.messages.create.return_value = mock_msg
    return mock_cls


# ---------------------------------------------------------------------------
# complete() tests
# ---------------------------------------------------------------------------

class TestLLMClientComplete:
    def test_returns_text_from_api(self, minimal_env, mock_anthropic_cls) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            client = LLMClient(settings=Settings())
            result = client.complete(system="You are helpful", user="Say hi")

        assert result == "test response"

    def test_passes_temperature_to_api(self, minimal_env, mock_anthropic_cls) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            client = LLMClient(settings=Settings())
            client.complete(system="sys", user="usr", temperature=0.1)

        kwargs = mock_anthropic_cls.return_value.messages.create.call_args[1]
        assert kwargs["temperature"] == 0.1

    def test_passes_system_and_user_to_api(self, minimal_env, mock_anthropic_cls) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            client = LLMClient(settings=Settings())
            client.complete(system="My system", user="My question")

        kwargs = mock_anthropic_cls.return_value.messages.create.call_args[1]
        assert kwargs["system"] == "My system"
        assert kwargs["messages"][0]["content"] == "My question"

    def test_uses_model_and_max_tokens_from_settings(
        self, minimal_env, mock_anthropic_cls, monkeypatch
    ) -> None:
        monkeypatch.setenv("ZER0_LLM_MODEL", "claude-test-model")
        monkeypatch.setenv("ZER0_LLM_MAX_TOKENS", "512")

        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            client = LLMClient(settings=Settings())
            client.complete(system="s", user="u")

        kwargs = mock_anthropic_cls.return_value.messages.create.call_args[1]
        assert kwargs["model"] == "claude-test-model"
        assert kwargs["max_tokens"] == 512


# ---------------------------------------------------------------------------
# load_prompt() tests
# ---------------------------------------------------------------------------

class TestLoadPrompt:
    def test_injects_config_variables_into_template(
        self, minimal_env, mock_anthropic_cls, tmp_path
    ) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        (tmp_path / "greet.md").write_text("Hi {{ company_name }}, tone: {{ tone }}")

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            with patch("zer0.llm.client._PROMPTS_DIR", tmp_path):
                client = LLMClient(settings=Settings())
                result = client.load_prompt("greet", _make_resolved_config())

        assert result == "Hi Acme, tone: professional"

    def test_unknown_placeholder_left_unchanged(
        self, minimal_env, mock_anthropic_cls, tmp_path
    ) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        (tmp_path / "tmpl.md").write_text("Hello {{ unknown_var }}")

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            with patch("zer0.llm.client._PROMPTS_DIR", tmp_path):
                client = LLMClient(settings=Settings())
                result = client.load_prompt("tmpl", _make_resolved_config())

        assert "{{ unknown_var }}" in result

    def test_extra_kwargs_override_defaults(
        self, minimal_env, mock_anthropic_cls, tmp_path
    ) -> None:
        from zer0.config.settings import Settings
        from zer0.llm.client import LLMClient

        (tmp_path / "tmpl.md").write_text("{{ lead_name }}")

        with patch("zer0.llm.client.anthropic.Anthropic", mock_anthropic_cls):
            with patch("zer0.llm.client._PROMPTS_DIR", tmp_path):
                client = LLMClient(settings=Settings())
                result = client.load_prompt("tmpl", _make_resolved_config(), lead_name="Alice")

        assert result == "Alice"
