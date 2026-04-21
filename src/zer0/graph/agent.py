"""Graph assembly — compile once at startup.

Spec: spec/product/05-agent-graph.md — Overview
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from zer0.graph.edges import (
    after_approval_gate,
    after_discover,
    after_follow_up_loop,
    after_qualify,
    after_resolve_config,
)
from zer0.graph.nodes import (
    node_approval_gate,
    node_discover,
    node_follow_up_loop,
    node_handle_error,
    node_outreach,
    node_qualify,
    node_research,
    node_resolve_config,
)
from zer0.graph.state import AgentState


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("resolve_config", node_resolve_config)
    g.add_node("discover", node_discover)
    g.add_node("research", node_research)
    g.add_node("qualify", node_qualify)
    g.add_node("approval_gate", node_approval_gate)
    g.add_node("outreach", node_outreach)
    g.add_node("follow_up_loop", node_follow_up_loop)
    g.add_node("handle_error", node_handle_error)

    g.add_edge(START, "resolve_config")
    g.add_conditional_edges("resolve_config", after_resolve_config, {"handle_error": "handle_error", "discover": "discover"})
    g.add_conditional_edges("discover", after_discover, {"handle_error": "handle_error", "research": "research", "end": END})
    g.add_edge("research", "qualify")
    g.add_conditional_edges("qualify", after_qualify, {"handle_error": "handle_error", "approval_gate": "approval_gate", "end": END})
    g.add_conditional_edges("approval_gate", after_approval_gate, {"handle_error": "handle_error", "outreach": "outreach", "end": END})
    g.add_edge("outreach", "follow_up_loop")
    g.add_conditional_edges("follow_up_loop", after_follow_up_loop, {"follow_up_loop": "follow_up_loop", "end": END})
    g.add_edge("handle_error", END)

    return g.compile()


# Singleton — compiled once at import time when the application starts.
agent_graph = build_graph()
