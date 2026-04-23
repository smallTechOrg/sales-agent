# Phase-7 gate (edges) — per spec/engineering/phases.md
from __future__ import annotations

from unittest.mock import MagicMock

from zer0.graph.edges import (
    after_approval_gate,
    after_check_replies,
    after_discover,
    after_qualify,
    after_resolve_config,
)


class TestAfterResolveConfig:
    def test_error_routes_to_handle_error(self) -> None:
        assert after_resolve_config({"error": "something went wrong"}) == "handle_error"

    def test_no_error_routes_to_discover(self) -> None:
        assert after_resolve_config({}) == "discover"

    def test_none_error_routes_to_discover(self) -> None:
        assert after_resolve_config({"error": None}) == "discover"


class TestAfterDiscover:
    def test_error_routes_to_handle_error(self) -> None:
        assert after_discover({"error": "fail"}) == "handle_error"

    def test_no_links_routes_to_end(self) -> None:
        assert after_discover({}) == "end"
        assert after_discover({"links": []}) == "end"

    def test_with_links_routes_to_scrape_links(self) -> None:
        from zer0.domain.link import Link, LinkSource

        lnk = Link(
            id="l1",
            campaign_id="c1",
            tenant_id="t1",
            url="https://x.com",
            source=LinkSource.web,
        )
        assert after_discover({"links": [lnk]}) == "scrape_links"


class TestAfterQualify:
    def test_error_routes_to_handle_error(self) -> None:
        assert after_qualify({"error": "fail"}) == "handle_error"

    def test_no_qualified_leads_routes_to_end(self) -> None:
        assert after_qualify({}) == "end"
        assert after_qualify({"leads": []}) == "end"

    def test_with_qualified_leads_routes_to_get_people(self) -> None:
        from zer0.domain.lead import Lead, LeadStage

        lead = Lead(
            id="l1",
            tenant_id="t1",
            campaign_id="c1",
            stage=LeadStage.qualification,
            company_name="Acme",
        )
        assert after_qualify({"leads": [lead]}) == "get_people"


class TestAfterApprovalGate:
    def test_error_routes_to_handle_error(self) -> None:
        assert after_approval_gate({"error": "fail"}) == "handle_error"

    def test_pending_people_pause_run_at_end(self) -> None:
        assert after_approval_gate({"pending_approval_person_ids": ["p1"]}) == "end"

    def test_no_approved_people_routes_to_end(self) -> None:
        assert after_approval_gate({}) == "end"
        assert after_approval_gate({"approved_person_ids": []}) == "end"

    def test_approved_people_route_to_outreach(self) -> None:
        state = {"approved_person_ids": ["p1"], "pending_approval_person_ids": []}
        assert after_approval_gate(state) == "outreach"


class TestAfterCheckReplies:
    def test_active_leads_stay_in_loop(self) -> None:
        msg = MagicMock()
        msg.lead_id = "l1"
        state = {"sent_messages": [msg], "completed_lead_ids": []}
        assert after_check_replies(state) == "check_replies"

    def test_all_completed_routes_to_end(self) -> None:
        msg = MagicMock()
        msg.lead_id = "l1"
        state = {"sent_messages": [msg], "completed_lead_ids": ["l1"]}
        assert after_check_replies(state) == "end"

    def test_no_messages_routes_to_end(self) -> None:
        assert after_check_replies({}) == "end"
        assert after_check_replies({"sent_messages": []}) == "end"

    def test_partial_completion_stays_in_loop(self) -> None:
        msg1, msg2 = MagicMock(), MagicMock()
        msg1.lead_id = "l1"
        msg2.lead_id = "l2"
        state = {"sent_messages": [msg1, msg2], "completed_lead_ids": ["l1"]}
        assert after_check_replies(state) == "check_replies"
