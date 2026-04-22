# Phase-7 gate (agent graph) — per spec/engineering/phases.md
from __future__ import annotations


class TestAgentGraph:
    def test_graph_compiles_without_error(self) -> None:
        from zer0.graph.agent import agent_graph

        assert agent_graph is not None

    def test_graph_contains_all_expected_nodes(self) -> None:
        from zer0.graph.agent import agent_graph

        expected = {
            "resolve_config",
            "discover",
            "scrape_links",
            "identify_leads",
            "research",
            "qualify",
            "get_contacts",
            "approval_gate",
            "outreach",
            "check_replies",
            "handle_error",
        }
        assert expected.issubset(set(agent_graph.nodes.keys()))
