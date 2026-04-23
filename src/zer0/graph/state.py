"""AgentState — LangGraph state schema.

Spec: spec/product/10-agent-graph.md — State schema
"""

from __future__ import annotations

from typing import TypedDict

from zer0.domain import Person, Lead, Link
from zer0.domain.config import ResolvedConfig
from zer0.domain.outreach import OutreachDraft, Reply, SentMessage


class AgentState(TypedDict, total=False):
    # --- Identity ---
    run_id: str
    tenant_id: str
    campaign_id: str
    config: ResolvedConfig

    # --- Discovery ---
    links: list[Link]

    # --- Pipeline ---
    leads: list[Lead]

    # --- People ---
    people: list[Person]

    # --- Approval gate ---
    pending_approval_person_ids: list[str]
    approved_person_ids: list[str]

    # --- Outreach ---
    outreach_drafts: list[OutreachDraft]
    sent_messages: list[SentMessage]
    replies: list[Reply]

    # --- Run control ---
    error: str | None
    completed_lead_ids: list[str]
