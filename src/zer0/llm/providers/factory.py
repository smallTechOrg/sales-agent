"""LLM provider factory.

Spec: spec/product/02-architecture.md — Module responsibilities / llm/

Creates LLM provider instances based on configuration.
Currently supports: gemini (default).

To add a new provider:
1. Create a new provider module in zer0/llm/providers/ (e.g., anthropic.py)
2. Implement the LLMProvider interface
3. Add the provider to the _PROVIDERS registry
4. Update the spec to document the new provider
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from zer0.llm.providers.base import LLMProvider

if TYPE_CHECKING:
    from zer0.config.settings import Settings

_PROVIDERS: dict[str, type[LLMProvider]] = {}


def _register_providers() -> None:
    """Register available providers lazily to avoid circular imports."""
    global _PROVIDERS
    if not _PROVIDERS:
        from zer0.llm.providers.gemini import GeminiProvider

        _PROVIDERS["gemini"] = GeminiProvider  # type: ignore[assignment]


def create_llm_client(provider: str | None = None, settings: Settings | None = None) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider: Provider name (e.g., "gemini", "anthropic"). Defaults to "gemini".
        settings: Optional Settings instance. If None, loads from environment.

    Returns:
        An LLMProvider instance.

    Raises:
        ValueError: If the provider is not supported.
    """
    _register_providers()

    if provider is None:
        provider = "gemini"

    provider_lower = provider.lower().strip()
    if provider_lower not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        msg = f"Unsupported LLM provider: {provider!r}. Available: {available}."
        raise ValueError(msg)

    provider_cls = _PROVIDERS[provider_lower]
    return provider_cls(settings=settings)


def register_provider(name: str, provider_cls: type[LLMProvider]) -> None:
    """Register a new provider at runtime.

    This allows adding providers before the factory is initialized.

    Args:
        name: Provider name (e.g., "anthropic").
        provider_cls: Provider class implementing LLMProvider.
    """
    global _PROVIDERS
    _PROVIDERS[name.lower().strip()] = provider_cls
