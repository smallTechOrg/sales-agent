"""duckduckgo_search adapter.

Spec: spec/product/04-capabilities/01-discovery.md — web source fallback chain
Input:  DiscoveryConfig + ICP
Output: list[RawLead]

No API key required. Used as fallback when Tavily key is not configured.
"""

from __future__ import annotations

import uuid

from duckduckgo_search import DDGS

from zer0.domain import DiscoveryConfig, ICP, LeadSource, RawLead


def duckduckgo_search(
    *,
    discovery_config: DiscoveryConfig,
    icp: ICP,
    tenant_id: str,
    campaign_id: str,
) -> list[RawLead]:
    """Keyword search via DuckDuckGo. No API key required."""
    leads: list[RawLead] = []

    with DDGS() as ddgs:
        for query_template in discovery_config.query_templates:
            query = query_template.format(
                industries=" OR ".join(icp.target_industries),
                roles=" OR ".join(icp.target_roles),
                geography=" OR ".join(icp.geography),
            )
            results = ddgs.text(query, max_results=discovery_config.volume_per_run)
            for result in (results or []):
                leads.append(
                    RawLead(
                        id=str(uuid.uuid4()),
                        campaign_id=campaign_id,
                        tenant_id=tenant_id,
                        company=None,
                        name=None,
                        url=result["href"],
                        source=LeadSource.web,
                    )
                )

    return leads
