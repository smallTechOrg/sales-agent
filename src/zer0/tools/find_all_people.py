"""find_all_people tool.

Spec: spec/product/04-capabilities/07-contact-discovery.md
Input:  Lead + target_roles
Output: list[Person] — people found at the company

NOTE: This is a stub. A real implementation would query a data provider
(e.g. Apollo, Hunter.io) or scrape LinkedIn. The stub returns an empty
list so the pipeline can proceed end-to-end in tests.
"""

from __future__ import annotations

import structlog

from zer0.domain import Person, Lead
from zer0.domain.config import ResolvedConfig

log = structlog.get_logger(__name__)


def find_all_people(
    *,
    lead: Lead,
    target_roles: list[str],
    config: ResolvedConfig,
) -> list[Person]:
    """Discover people at the lead's company matching the target roles.

    Returns an empty list until a provider integration is wired in.
    """
    log.info(
        "find_all_people.stub",
        lead_id=lead.id,
        company=lead.company_name,
        target_roles=target_roles,
    )
    return []