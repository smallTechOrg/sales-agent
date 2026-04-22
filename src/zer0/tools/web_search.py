"""web_search tool — Tavily adapter.

Spec: spec/product/04-capabilities/01-discovery.md — web source
Input:  DiscoveryConfig + ICP
Output: list[RawLead]

Query templates use {{roles}}, {{industries}}, {{geography}}, {{keywords}},
{{company_size}} placeholders — see _query_render.py for full reference.
"""

from __future__ import annotations

import uuid

from tavily import TavilyClient  # type: ignore[import-untyped]

from zer0.domain import DiscoveryConfig, ICP
from zer0.tools._query_render import render_query


class _UrlResult:
    """Minimal container so node_discover can call getattr(r, 'url', None)."""
    def __init__(self, url: str) -> None:
        self.url = url


def web_search(
    *,
    discovery_config: DiscoveryConfig,
    icp: ICP,
    tenant_id: str,
    campaign_id: str,
    tavily_api_key: str,
) -> list[_UrlResult]:
    """Keyword search via Tavily to discover leads matching the ICP."""
    client = TavilyClient(api_key=tavily_api_key)
    results_out: list[_UrlResult] = []

    for template in discovery_config.query_templates:
        query = render_query(template, discovery_config, icp)
        results = client.search(query=query, max_results=discovery_config.volume_per_run)
        for result in results.get("results", []):
            results_out.append(_UrlResult(url=result["url"]))

    return results_out
