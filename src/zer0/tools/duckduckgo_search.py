"""duckduckgo_search adapter.

Spec: spec/product/04-capabilities/01-discovery.md — web source
Input:  DiscoveryConfig + ICP
Output: list[RawLead]

No API key required. Always runs alongside any other configured web adapters.

Query templates use {{roles}}, {{industries}}, {{geography}}, {{keywords}},
{{company_size}} placeholders — see _query_render.py for full reference.
"""

from __future__ import annotations

import uuid

from ddgs import DDGS  # type: ignore[import-untyped]

from zer0.domain import DiscoveryConfig, ICP, LeadSource, RawLead
from zer0.tools._query_render import render_query


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
        for template in discovery_config.query_templates:
            query = render_query(template, discovery_config, icp)
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
