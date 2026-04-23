"""linkedin_search tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  DiscoveryConfig + ICP
Output: list[RawLead]
"""

from __future__ import annotations

import uuid

from zer0.domain import DiscoveryConfig, ICP


class _UrlResult:
    """Minimal container so node_discover can call getattr(r, 'url', None)."""
    def __init__(self, url: str) -> None:
        self.url = url


def linkedin_search(
    *,
    discovery_config: DiscoveryConfig,
    icp: ICP,
    tenant_id: str,
    campaign_id: str,
) -> list[_UrlResult]:
    """Search LinkedIn for companies and people matching the ICP.

    TODO: Integrate with LinkedIn API / scraping layer.
    """
    raise NotImplementedError("linkedin_search — integration not implemented")
