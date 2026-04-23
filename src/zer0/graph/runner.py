"""Campaign runner — entry point for the scheduler and API.

Spec: spec/product/05-agent-graph.md — Overview
"""

from __future__ import annotations

import uuid

import structlog

from zer0.db.models import LinkRow
from zer0.db.session import create_db_session
from zer0.domain import Link, LinkSource
from zer0.graph.agent import agent_graph
from zer0.graph.state import AgentState

log = structlog.get_logger(__name__)


def _preload_links(campaign_id: str, tenant_id: str) -> list[Link]:
    """Load all existing LinkRows for this tenant from DB into domain objects.

    Tenant-scoped (not campaign-scoped) because links are now deduplicated by
    (tenant_id, url). The discover node still filters by campaign via link_leads,
    but the in-memory state carries all tenant links so the dedup set is correct.
    """
    try:
        with create_db_session() as session:
            rows = (
                session.query(LinkRow)
                .filter(LinkRow.tenant_id == tenant_id)
                .all()
            )
            links = []
            for row in rows:
                try:
                    source = LinkSource(row.source)
                except ValueError:
                    source = LinkSource.web
                links.append(Link(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    campaign_id=row.campaign_id,
                    url=row.url,
                    source=source,
                    page_text=row.page_text,
                    scraped_at=row.scraped_at,
                    identified_at=row.identified_at,
                ))
        log.info("runner.links_preloaded", campaign_id=campaign_id, count=len(links))
        return links
    except Exception as exc:
        log.warning("runner.preload_failed", campaign_id=campaign_id, error=str(exc))
        return []


def run_campaign(*, campaign_id: str, tenant_id: str, run_id: str | None = None) -> AgentState:
    """Invoke the agent graph for a single campaign run.

    Returns the final AgentState. Supply run_id from the API trigger so the
    same ID appears in event logs and the trigger response.
    """
    import uuid as _uuid

    existing_links = _preload_links(campaign_id=campaign_id, tenant_id=tenant_id)

    initial: AgentState = {
        "run_id": run_id or str(_uuid.uuid4()),
        "campaign_id": campaign_id,
        "tenant_id": tenant_id,
        "links": existing_links,
        "leads": [],
        "people": [],
        "pending_approval_person_ids": [],
        "approved_person_ids": [],
        "outreach_drafts": [],
        "sent_messages": [],
        "replies": [],
        "completed_lead_ids": [],
        "error": None,
    }

    log.info("campaign.run_started", campaign_id=campaign_id, tenant_id=tenant_id, run_id=initial["run_id"])

    final_state: AgentState = agent_graph.invoke(initial)

    log.info(
        "campaign.run_finished",
        campaign_id=campaign_id,
        run_id=initial["run_id"],
        links_discovered=len(final_state.get("links", [])),
        leads_found=len(final_state.get("leads", [])),
        messages_sent=len(final_state.get("sent_messages", [])),
    )

    return final_state
