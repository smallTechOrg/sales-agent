"""Abstract base class for LLM providers.

Spec: spec/product/02-architecture.md — Module responsibilities / llm/
Spec: spec/product/05-config.md — LLM configuration

All LLM providers must implement this interface to support the factory pattern
for easy swapping between providers (Gemini, Anthropic, OpenAI, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, settings: Any = None) -> None:
        """Initialize the provider with optional settings.

        Args:
            settings: Optional Settings instance.
        """
        pass

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str:
        """Send a system+user prompt pair and return the text response.

        Args:
            system: System prompt instructions.
            user: User message content.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            The generated text response.
        """
        ...

    @abstractmethod
    def load_prompt(
        self,
        name: str,
        config: Any,
        **extra: Any,
    ) -> str:
        """Load a prompt template and inject variables.

        Args:
            name: Prompt template name (without .md extension).
            config: ResolvedConfig object with variables.
            **extra: Additional variables to inject.

        Returns:
            The rendered prompt with variables substituted.
        """
        ...
