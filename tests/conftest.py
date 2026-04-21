"""Shared pytest fixtures.

Spec: spec/engineering/phases.md — every test phase builds on this foundation.
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

# One Fernet key generated at collection time — reused across all tests.
_TEST_FERNET_KEY: str = Fernet.generate_key().decode()

MINIMAL_ENV: dict[str, str] = {
    "ZER0_DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
    "ZER0_ANTHROPIC_API_KEY": "sk-ant-test-key",
    "ZER0_TAVILY_API_KEY": "tvly-test-key",
    "ZER0_JWT_SECRET": "test-jwt-secret-value",
    "ZER0_CREDENTIAL_ENCRYPTION_KEY": _TEST_FERNET_KEY,
}


@pytest.fixture(autouse=True)
def _reset_settings_singleton():
    """Reset the Settings singleton before and after every test so env patches
    are always picked up by the next Settings() constructor call."""
    import zer0.config.settings as _m

    _m._settings = None
    yield
    _m._settings = None


@pytest.fixture
def minimal_env(monkeypatch):
    """Populate the minimum required ZER0_ environment variables."""
    for key, value in MINIMAL_ENV.items():
        monkeypatch.setenv(key, value)
    return MINIMAL_ENV
