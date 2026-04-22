"""enrich_lead tool.

Spec: spec/product/04-capabilities/02-enrichment.md — Sub-step 3
Input:  Lead + research_sources (list of freshly scraped page texts) + ICP
Output: Lead with research_summary and signals appended (cumulative)

Research sources come from an independent web search about the company
(node_research fetches them via web_search + scrape_page before calling here).
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
    research_sources: list[str],
    icp: ICP,
    llm: LLMClient,
    config: ResolvedConfig,
) -> Lead:
    """Append research signals from fresh web-search results (cumulative).

    research_sources is a list of scraped page texts fetched specifically for
    this company — not the original discovery page. The LLM synthesises them
    into a company summary and buying signals. Results are APPENDED to existing
    research_summary / signals, never overwritten.
    """
    system = llm.load_prompt("researcher", config)

    combined_sources = "\n\n---\n\n".join(src[:3000] for src in research_sources[:5] if src)
    if not combined_sources:
        combined_sources = "(no research pages available)"

    user = (
        f"Company: {lead.company_name or 'unknown'}\n"
        f"Domain: {lead.domain or 'unknown'}\n\n"
        f"Research sources (web search results):\n{combined_sources}\n\n"
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
    existing_signals = list(lead.signals or [])
    merged_signals = existing_signals + [s for s in new_signals if s not in existing_signals]

    return lead.model_copy(update={
        "research_summary": updated_summary,
        "signals": merged_signals,
        "last_researched_at": datetime.now(tz=timezone.utc),
    })

