"""detect_language tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  EnrichedLead
Output: ISO 639-1 language code (str)

Uses the LLM to detect language from company_summary / role_summary.
Falls back to "en" on any error.
"""

from __future__ import annotations

from zer0.domain import Lead
from zer0.domain.config import ResolvedConfig
from zer0.llm.client import LLMClient

_FALLBACK = "en"


def detect_language(
    *,
    lead: Lead,
    llm: LLMClient,
    config: ResolvedConfig,
) -> str:
    """Return ISO 639-1 language code detected from the lead's text data."""
    text = " ".join(
        filter(None, [lead.research_summary, *lead.signals])
    )
    if not text.strip():
        return _FALLBACK

    system = "You detect the natural language of a text. Reply with only a 2-letter ISO 639-1 code, nothing else."
    user = f"What language is this text in?\n\n{text[:1000]}"

    try:
        result = llm.complete(system=system, user=user).strip().lower()
        # Accept only a 2-letter alpha code.
        if len(result) == 2 and result.isalpha():
            return result
    except Exception:
        pass

    return _FALLBACK
