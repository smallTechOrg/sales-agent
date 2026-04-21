"""directory_search tool — IndiaMART/Justdial fallback.

Spec: spec/product/02-architecture.md — Tools table
Input:  DiscoveryConfig + ICP
Output: list[RawLead]
"""

from __future__ import annotations

from zer0.domain import DiscoveryConfig, ICP, RawLead


def directory_search(
    *,
    discovery_config: DiscoveryConfig,
    icp: ICP,
    tenant_id: str,
    campaign_id: str,
) -> list[RawLead]:
    """Search IndiaMART / Justdial directories for matching companies.

    TODO: Integrate with IndiaMART API and/or Justdial scraping.
    """
    raise NotImplementedError("directory_search — integration not implemented")
