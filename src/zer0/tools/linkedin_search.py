"""linkedin_search tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  DiscoveryConfig + ICP
Output: list[RawLead]
"""

from __future__ import annotations

import uuid

from zer0.domain import DiscoveryConfig, ICP, RawLead, LeadSource


def linkedin_search(
    *,
    discovery_config: DiscoveryConfig,
    icp: ICP,
    tenant_id: str,
    campaign_id: str,
) -> list[RawLead]:
    """Search LinkedIn for companies and contacts matching the ICP.

    TODO: Integrate with LinkedIn API / scraping layer.
    Returns raw, un-enriched leads with URL populated.
    """
    raise NotImplementedError("linkedin_search — integration not implemented")
