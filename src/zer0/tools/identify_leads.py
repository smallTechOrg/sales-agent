"""identify_leads tool.

Spec: spec/product/04-capabilities/02-enrichment.md — identify stage
Input:  Link (with page_text) + ICP
Output: list[Lead] — one Lead per company entity found on the page
"""

from __future__ import annotations

import json
import re

import structlog

from zer0.domain import ICP, Lead, Link
from zer0.domain.config import ResolvedConfig
from zer0.domain.lead import LeadStage
from zer0.llm.client import LLMClient

log = structlog.get_logger(__name__)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


def identify_leads(
    *,
    link: Link,
    icp: ICP,
    llm: LLMClient,
    config: ResolvedConfig,
) -> list[Lead]:
    """Extract company entities from a scraped page and return a Lead for each.

    A single directory page may list many companies — the LLM identifies each one.
    """
    if not link.page_text:
        log.warning("identify_leads.no_page_text", link_id=link.id, url=link.url)
        return []

    system = llm.load_prompt("identifier", config)
    user = (
        f"Page URL: {link.url}\n\n"
        f"Page text:\n{link.page_text[:8000]}\n\n"
        f"ICP target industries: {', '.join(icp.target_industries)}\n"
        f"ICP target company size: {icp.company_size_range.min} – {icp.company_size_range.max} employees\n\n"
        "Return a JSON array of objects, one per company. Each object must have:\n"
        "  company_name (str), domain (str|null), industry (str|null),\n"
        "  headcount_range (str|null), business_type (str|null)\n"
        "Return only valid JSON — no markdown, no commentary."
    )

    raw = llm.complete(system=system, user=user)

    try:
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        entries: list[dict] = json.loads(text)
        if not isinstance(entries, list):
            entries = []
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("identify_leads.parse_error", link_id=link.id, error=str(exc), raw=raw[:200])
        entries = []

    leads: list[Lead] = []
    for entry in entries:
        company_name = entry.get("company_name")
        if not company_name:
            continue
        lead = Lead(
            id=_new_id(),
            tenant_id=link.tenant_id,
            campaign_id=link.campaign_id,
            link_id=link.id,
            stage=LeadStage.prospect,
            company_name=company_name,
            domain=entry.get("domain"),
            industry=entry.get("industry"),
            headcount_range=entry.get("headcount_range"),
            business_type=entry.get("business_type"),
        )
        leads.append(lead)

    log.info("identify_leads.done", link_id=link.id, count=len(leads))
    return leads
