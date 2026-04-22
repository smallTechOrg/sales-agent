"""Google Gemini LLM provider implementation.

Spec: spec/product/02-architecture.md — Module responsibilities / llm/
Spec: spec/engineering/tech-stack.md — google-genai>=1.0

Wraps the Google Gen AI SDK to:
- Enforce the configured model and token limits from Settings.
- Load prompt templates from src/zer0/prompts/*.md.
- Inject ResolvedConfig variables into prompt placeholders.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from google import genai
from google.genai import types

if TYPE_CHECKING:
    from zer0.config.settings import Settings
    from zer0.domain.config import ResolvedConfig

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


class GeminiProvider:
    """LLM provider implementation for Google Gemini."""

    def __init__(self, settings: Settings | None = None) -> None:
        if settings is None:
            from zer0.config.settings import get_settings

            settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens

    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.3,
    ) -> str:
        """Send a system+user prompt pair and return the text response."""
        response = self._client.models.generate_content(
            model=self._model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=self._max_tokens,
            ),
        )
        return response.text  # type: ignore[return-value]

    def load_prompt(
        self,
        name: str,
        config: ResolvedConfig,
        **extra: Any,
    ) -> str:
        """Load a prompt template from prompts/<name>.md and inject variables.

        Variables are injected as {{ key }} placeholders. All ResolvedConfig
        fields are available by default; extra kwargs override or add variables.
        """
        path = _PROMPTS_DIR / f"{name}.md"
        template = path.read_text(encoding="utf-8")

        variables: dict[str, Any] = {
            "company_name": config.offering_name,
            "offering_name": config.offering_name,
            "value_proposition": config.value_proposition,
            "pain_points": "\n".join(f"- {p}" for p in config.pain_points),
            "target_industries": ", ".join(config.icp.target_industries),
            "target_roles": ", ".join(config.icp.target_roles),
            "min_employees": str(config.icp.company_size_range.min),
            "max_employees": str(config.icp.company_size_range.max),
            "tone": config.outreach_config.tone,
            "language": config.outreach_config.language_default,
            **extra,
        }

        def replace(m: re.Match[str]) -> str:
            key = m.group(1).strip()
            return str(variables.get(key, m.group(0)))

        return re.sub(r"\{\{\s*(\w+)\s*\}\}", replace, template)
