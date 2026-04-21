"""enrich_lead tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  RawLead + ICP + scraped page text + contact details
Output: EnrichedLead
"""

from __future__ import annotations

import json

from zer0.domain import EnrichedLead, ICP, RawLead
from zer0.domain.config import ResolvedConfig
from zer0.llm.client import LLMClient


def enrich_lead(
    *,
    raw_lead: RawLead,
    icp: ICP,
    page_text: str,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    contact_role: str | None,
    llm: LLMClient,
    config: ResolvedConfig,
) -> EnrichedLead:
    """Combine scraped page text and contact details into an EnrichedLead via LLM.

    The LLM extracts company summary, role summary, and recent signals
    relevant to the ICP from the raw page text.
    """
    system = llm.load_prompt("researcher", config)
    user = (
        f"Company URL: {raw_lead.url}\n\n"
        f"Page text:\n{page_text[:6000]}\n\n"
        f"Target roles: {', '.join(icp.target_roles)}\n"
        f"Target industries: {', '.join(icp.target_industries)}\n\n"
        "Return JSON with keys: company_summary, role_summary, recent_signals (list of strings)."
    )

    raw = llm.complete(system=system, user=user)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {}

    base = raw_lead.model_dump()
    base["name"] = contact_name or raw_lead.name
    return EnrichedLead(
        **base,
        company_summary=parsed.get("company_summary"),
        role_summary=parsed.get("role_summary"),
        recent_signals=parsed.get("recent_signals", []),
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_role=contact_role,
    )
