"""Campaign runner — entry point for the scheduler and API.

Spec: spec/product/05-agent-graph.md — Overview
"""

from __future__ import annotations

import uuid

import structlog

from zer0.graph.agent import agent_graph
from zer0.graph.state import AgentState

log = structlog.get_logger(__name__)


def run_campaign(*, campaign_id: str, tenant_id: str) -> AgentState:
    """Invoke the agent graph for a single campaign run.

    Returns the final AgentState after the run completes (or parks at approval gate).
    """
    initial: AgentState = {
        "run_id": str(uuid.uuid4()),
        "campaign_id": campaign_id,
        "tenant_id": tenant_id,
        "raw_leads": [],
        "enriched_leads": [],
        "qualified_leads": [],
        "rejected_leads": [],
        "pending_approval_lead_ids": [],
        "approved_lead_ids": [],
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
        leads_discovered=len(final_state.get("raw_leads", [])),
        leads_qualified=len(final_state.get("qualified_leads", [])),
        messages_sent=len(final_state.get("sent_messages", [])),
    )

    return final_state
