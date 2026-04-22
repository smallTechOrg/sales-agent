"""LLM client factory wrapper.

Spec: spec/product/02-architecture.md — Module responsibilities / llm/
Spec: spec/product/05-config.md — LLM configuration

This module provides backward compatibility by wrapping the factory-created provider.
The actual LLM client is created via create_llm_client() which loads the configured provider.

For new code, import create_llm_client directly from zer0.llm.providers instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zer0.llm.providers.base import LLMProvider
from zer0.llm.providers.factory import create_llm_client

if TYPE_CHECKING:
    from zer0.config.settings import Settings
    from zer0.domain.config import ResolvedConfig


class LLMClient:
    """LLM client backed by a configurable provider.

    This class delegates to the provider created via create_llm_client().
    By default, it uses the provider configured in Settings.llm_provider.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        from zer0.config.settings import get_settings

        if settings is None:
            settings = get_settings()
        self._provider: LLMProvider = create_llm_client(
            provider=settings.llm_provider,
            settings=settings,
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str:
        """Send a system+user prompt pair and return the text response."""
        return self._provider.complete(system=system, user=user, temperature=temperature)

    def load_prompt(
        self,
        name: str,
        config: ResolvedConfig,
        **extra: Any,
    ) -> str:
        """Load a prompt template from prompts/<name>.md and inject variables."""
        return self._provider.load_prompt(name, config, **extra)
