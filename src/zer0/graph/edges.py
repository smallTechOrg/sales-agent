"""Graph edges — conditional routing functions.

Spec: spec/product/05-agent-graph.md — Edges
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
    if not state.get("raw_leads"):
        return "end"
    return "research"


def after_qualify(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    if not state.get("qualified_leads"):
        return "end"
    return "approval_gate"


def after_approval_gate(state: AgentState) -> str:
    if state.get("error"):
        return "handle_error"
    if state.get("pending_approval_lead_ids"):
        # Parked — run ends; resumed by API call
        return "end"
    if not state.get("approved_lead_ids"):
        return "end"
    return "outreach"


def after_follow_up_loop(state: AgentState) -> str:
    sent = state.get("sent_messages", [])
    completed = set(state.get("completed_lead_ids", []))
    active_ids = {m.lead_id for m in sent if m.lead_id not in completed}
    if active_ids:
        return "follow_up_loop"
    return "end"
