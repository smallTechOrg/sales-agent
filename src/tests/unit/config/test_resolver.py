# Phase-2 gate (resolver) — per spec/engineering/phases.md
from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from unittest.mock import MagicMock

from zer0.config.resolver import ConfigResolutionError, ConfigResolver, _decrypt_optional


# ---------------------------------------------------------------------------
# Helpers — build minimal ORM row mocks
# ---------------------------------------------------------------------------

def _make_campaign(**overrides):
    row = MagicMock()
    row.id = overrides.get("id", "c1")
    row.tenant_id = overrides.get("tenant_id", "t1")
    row.offering_id = overrides.get("offering_id", "o1")
    row.deleted_at = None
    row.approval_mode = overrides.get("approval_mode", None)
    row.volume_cap = None
    row.schedule = None
    row.discovery_override = None
    row.icp_override = None
    row.qualification_override = None
    row.outreach_override = None
    return row


def _make_offering(**overrides):
    row = MagicMock()
    row.id = overrides.get("id", "o1")
    row.tenant_id = overrides.get("tenant_id", "t1")
    row.deleted_at = None
    row.name = overrides.get("name", "Acme SaaS")
    row.value_proposition = overrides.get("value_proposition", "Save time")
    row.pain_points = []
    row.discovery_config = {
        "sources": ["web"],
        "query_templates": ["Find {company}"],
        "geography": ["US"],
        "volume_per_run": 10,
    }
    row.icp = {
        "target_industries": ["SaaS"],
        "target_roles": ["CTO"],
        "company_size_range": {"min": 10, "max": 500},
        "geography": ["US"],
        "keywords": [],
        "negative_keywords": [],
    }
    row.qualification_config = {
        "rubric_criteria": [{"name": "fit", "description": "Good fit", "weight": 1.0}],
        "score_threshold": 50.0,
        "disqualifying_signals": [],
    }
    row.outreach_config = {
        "channels_enabled": ["email"],
        "tone": "professional",
        "language_default": "en",
        "templates": {"first_touch": "Hello"},
        "follow_up_count": 2,
        "follow_up_spacing_days": 3,
        "send_schedule": "09:00-17:00 Mon-Fri",
    }
    return row


def _make_tenant(**overrides):
    row = MagicMock()
    row.id = overrides.get("id", "t1")
    row.deleted_at = None
    row.google_oauth_token_enc = None
    row.whatsapp_api_key_enc = None
    row.slack_webhook_url_enc = None
    return row


def _make_db(*results):
    """Build a mock Session whose .query().filter().first() returns results in order."""
    db = MagicMock()
    first_iter = iter(results)

    db.query.return_value.filter.return_value.first.side_effect = (
        lambda: next(first_iter)
    )
    return db


# ---------------------------------------------------------------------------
# ConfigResolver tests
# ---------------------------------------------------------------------------

class TestConfigResolver:
    def test_raises_when_campaign_not_found(self) -> None:
        db = _make_db(None)
        with pytest.raises(ConfigResolutionError, match="Campaign"):
            ConfigResolver(db).resolve("c1", "t1")

    def test_raises_when_offering_not_found(self) -> None:
        db = _make_db(_make_campaign(), None)
        with pytest.raises(ConfigResolutionError, match="Offering"):
            ConfigResolver(db).resolve("c1", "t1")

    def test_raises_when_tenant_not_found(self) -> None:
        db = _make_db(_make_campaign(), _make_offering(), None)
        with pytest.raises(ConfigResolutionError, match="Tenant"):
            ConfigResolver(db).resolve("c1", "t1")

    def test_resolve_returns_resolved_config(self) -> None:
        db = _make_db(_make_campaign(), _make_offering(), _make_tenant())
        config = ConfigResolver(db).resolve("c1", "t1")
        assert config.tenant_id == "t1"
        assert config.campaign_id == "c1"
        assert config.offering_name == "Acme SaaS"

    def test_resolve_defaults_approval_mode_to_full_auto(self) -> None:
        from zer0.domain.config import ApprovalMode

        db = _make_db(_make_campaign(approval_mode=None), _make_offering(), _make_tenant())
        config = ConfigResolver(db).resolve("c1", "t1")
        assert config.approval_mode == ApprovalMode.full_auto

    def test_campaign_approval_mode_is_respected(self) -> None:
        from zer0.domain.config import ApprovalMode

        db = _make_db(
            _make_campaign(approval_mode="approve_all"),
            _make_offering(),
            _make_tenant(),
        )
        config = ConfigResolver(db).resolve("c1", "t1")
        assert config.approval_mode == ApprovalMode.approve_all


# ---------------------------------------------------------------------------
# _decrypt_optional tests
# ---------------------------------------------------------------------------

class TestDecryptOptional:
    def test_none_input_returns_none(self) -> None:
        assert _decrypt_optional(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert _decrypt_optional("") is None

    def test_missing_env_key_returns_none(self, monkeypatch) -> None:
        monkeypatch.delenv("ZER0_CREDENTIAL_ENCRYPTION_KEY", raising=False)
        assert _decrypt_optional("some-value") is None

    def test_valid_roundtrip(self) -> None:
        key = Fernet.generate_key()
        token = Fernet(key).encrypt(b"secret").decode()

        original = os.environ.get("ZER0_CREDENTIAL_ENCRYPTION_KEY")
        os.environ["ZER0_CREDENTIAL_ENCRYPTION_KEY"] = key.decode()
        try:
            assert _decrypt_optional(token) == "secret"
        finally:
            if original is None:
                os.environ.pop("ZER0_CREDENTIAL_ENCRYPTION_KEY", None)
            else:
                os.environ["ZER0_CREDENTIAL_ENCRYPTION_KEY"] = original
