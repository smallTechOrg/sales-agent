"""Graph edges — conditional routing functions.

Spec: spec/product/10-agent-graph.md — Edges
"""

from __future__ import annotations

from zer0.graph.state import AgentState


def after_resolve_config(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    return "discover"


def after_discover(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    if not state.get("links"):
        return "end"
    return "scrape_links"


def after_scrape_links(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    return "identify_leads"


def after_identify_leads(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    if not state.get("leads"):
        return "end"
    return "research"


def after_research(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    return "qualify"


def after_qualify(state: AgentState) -> str:
    from zer0.domain.lead import LeadStage
    if state.get("error"):
        return "handle_error"
    qualified = [l for l in state.get("leads", []) if l.stage == LeadStage.qualification]
    if not qualified:
        return "end"
    return "get_people"


def after_get_people(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    if not state.get("people"):
        return "end"
    return "approval_gate"


def after_approval_gate(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    if state.get("pending_approval_person_ids"):
        return "end"
    if not state.get("approved_person_ids"):
        return "end"
    return "outreach"


def after_check_replies(state: AgentState) -> str:
    sent = state.get("sent_messages", [])
    completed = set(state.get("completed_lead_ids", []))
    active = [m for m in sent if getattr(m, "lead_id", None) not in completed]
    if active:
        return "check_replies"
    return "end"
