"""AgentState — LangGraph state schema.

Spec: spec/product/05-agent-graph.md — State schema
"""

from __future__ import annotations

from typing import TypedDict

from zer0.domain import (
    EnrichedLead,
    QualifiedLead,
    RawLead,
    RejectedLead,
)
from zer0.domain.config import ResolvedConfig
from zer0.domain.outreach import OutreachDraft, Reply, SentMessage


class AgentState(TypedDict, total=False):
    # --- Identity ---
    run_id: str
    tenant_id: str
    campaign_id: str
    config: ResolvedConfig

    # --- Discovery ---
    raw_leads: list[RawLead]

    # --- Per-lead pipeline ---
    enriched_leads: list[EnrichedLead]
    qualified_leads: list[QualifiedLead]
    rejected_leads: list[RejectedLead]

    # --- Approval gate ---
    pending_approval_lead_ids: list[str]
    approved_lead_ids: list[str]

    # --- Outreach ---
    outreach_drafts: list[OutreachDraft]
    sent_messages: list[SentMessage]
    replies: list[Reply]

    # --- Run control ---
    error: str | None
    completed_lead_ids: list[str]
