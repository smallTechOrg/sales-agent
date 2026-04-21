"""web_search tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  DiscoveryConfig + ICP
Output: list[RawLead]
Uses Tavily for keyword search.
"""

from __future__ import annotations

import uuid

from tavily import TavilyClient  # type: ignore[import-untyped]

from zer0.domain import DiscoveryConfig, ICP, LeadSource, RawLead


def web_search(
    *,
    discovery_config: DiscoveryConfig,
    icp: ICP,
    tenant_id: str,
    campaign_id: str,
    tavily_api_key: str,
) -> list[RawLead]:
    """Keyword search via Tavily to discover leads matching the ICP."""
    client = TavilyClient(api_key=tavily_api_key)
    leads: list[RawLead] = []

    for query_template in discovery_config.query_templates:
        query = query_template.format(
            industries=" OR ".join(icp.target_industries),
            roles=" OR ".join(icp.target_roles),
            geography=" OR ".join(icp.geography),
        )
        results = client.search(query=query, max_results=discovery_config.volume_per_run)
        for result in results.get("results", []):
            leads.append(
                RawLead(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign_id,
                    tenant_id=tenant_id,
                    company=None,
                    name=None,
                    url=result["url"],
                    source=LeadSource.web,
                )
            )

    return leads
