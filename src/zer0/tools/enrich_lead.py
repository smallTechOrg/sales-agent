"""enrich_lead tool.

Spec: spec/product/04-capabilities/02-enrichment.md
Input:  Lead + page_text (pre-scraped) + ICP
Output: Lead with research_summary and signals appended (cumulative)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from zer0.domain import ICP, Lead
from zer0.domain.config import ResolvedConfig
from zer0.llm.client import LLMClient


def enrich_lead(
    *,
    lead: Lead,
    page_text: str,
    icp: ICP,
    llm: LLMClient,
    config: ResolvedConfig,
) -> Lead:
    """Append research signals from page text to the lead (cumulative).

    The LLM extracts a company summary and signals relevant to the ICP.
    Results are *appended* to existing research_summary / signals — never overwritten.
    """
    system = llm.load_prompt("researcher", config)
    user = (
        f"Company: {lead.company_name or 'unknown'}\n"
        f"Domain: {lead.domain or 'unknown'}\n\n"
        f"Page text:\n{page_text[:6000]}\n\n"
        f"Target roles: {', '.join(icp.target_roles)}\n"
        f"Target industries: {', '.join(icp.target_industries)}\n\n"
        "Return JSON with keys: company_summary (str), recent_signals (list[str])."
    )

    raw = llm.complete(system=system, user=user)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {}

    new_summary: str = parsed.get("company_summary", "")
    new_signals: list[str] = parsed.get("recent_signals", [])

    updated_summary = "\n\n".join(filter(None, [lead.research_summary, new_summary])) or None
    updated_signals = list(lead.signals) + new_signals

    return lead.model_copy(update={
        "research_summary": updated_summary,
        "signals": updated_signals,
        "last_researched_at": datetime.now(tz=timezone.utc),
    })
