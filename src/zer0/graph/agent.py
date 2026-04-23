"""Graph assembly — compile once at startup.

Spec: spec/product/10-agent-graph.md — Topology
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from zer0.graph.edges import (
    after_approval_gate,
    after_check_replies,
    after_discover,
    after_get_people,
    after_identify_leads,
    after_qualify,
    after_research,
    after_resolve_config,
    after_scrape_links,
)
from zer0.graph.nodes import (
    node_approval_gate,
    node_check_replies,
    node_discover,
    node_get_people,
    node_handle_error,
    node_identify_leads,
    node_outreach,
    node_qualify,
    node_research,
    node_resolve_config,
    node_scrape_links,
)
from zer0.graph.state import AgentState


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("resolve_config", node_resolve_config)
    g.add_node("discover", node_discover)
    g.add_node("scrape_links", node_scrape_links)
    g.add_node("identify_leads", node_identify_leads)
    g.add_node("research", node_research)
    g.add_node("qualify", node_qualify)
    g.add_node("get_people", node_get_people)
    g.add_node("approval_gate", node_approval_gate)
    g.add_node("outreach", node_outreach)
    g.add_node("check_replies", node_check_replies)
    g.add_node("handle_error", node_handle_error)

    g.add_edge(START, "resolve_config")
    g.add_conditional_edges("resolve_config", after_resolve_config, {"handle_error": "handle_error", "discover": "discover"})
    g.add_conditional_edges("discover", after_discover, {"handle_error": "handle_error", "scrape_links": "scrape_links", "end": END})
    g.add_conditional_edges("scrape_links", after_scrape_links, {"handle_error": "handle_error", "identify_leads": "identify_leads"})
    g.add_conditional_edges("identify_leads", after_identify_leads, {"handle_error": "handle_error", "research": "research", "end": END})
    g.add_conditional_edges("research", after_research, {"handle_error": "handle_error", "qualify": "qualify"})
    g.add_conditional_edges("qualify", after_qualify, {"handle_error": "handle_error", "get_people": "get_people", "end": END})
    g.add_conditional_edges("get_people", after_get_people, {"handle_error": "handle_error", "approval_gate": "approval_gate", "end": END})
    g.add_conditional_edges("approval_gate", after_approval_gate, {"handle_error": "handle_error", "outreach": "outreach", "end": END})
    g.add_edge("outreach", "check_replies")
    g.add_conditional_edges("check_replies", after_check_replies, {"check_replies": "check_replies", "end": END})
    g.add_edge("handle_error", END)

    return g.compile()


# Singleton — compiled once at import time when the application starts.
agent_graph = build_graph()
