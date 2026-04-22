# Phase-8 gate — API integration tests
# Spec: spec/engineering/phases.md § Phase 8
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _no_db():
    """Stub get_session — yields a MagicMock so no DB is needed."""
    yield MagicMock()


@pytest.fixture
def app(minimal_env):
    """Create a fresh FastAPI application with the DB dependency stubbed out."""
    from zer0.api import create_app
    from zer0.db.session import get_session

    application = create_app()
    application.dependency_overrides[get_session] = _no_db
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


class TestHealth:
    def test_returns_200(self, client) -> None:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_body_matches_envelope(self, client) -> None:
        body = client.get("/api/v1/health").json()
        assert body == {"data": {"status": "ok"}, "error": None}


class TestAuthTokenFormat:
    """Validates POST /auth/token request-body schema — {tenant_id, secret}."""

    def test_empty_body_returns_422(self, client) -> None:
        resp = client.post("/api/v1/auth/token", json={})
        assert resp.status_code == 422

    def test_missing_secret_returns_422(self, client) -> None:
        resp = client.post("/api/v1/auth/token", json={"tenant_id": "t1"})
        assert resp.status_code == 422

    def test_missing_tenant_id_returns_422(self, client) -> None:
        resp = client.post("/api/v1/auth/token", json={"secret": "s"})
        assert resp.status_code == 422

    def test_unknown_tenant_returns_404(self, app) -> None:
        from zer0.db.session import get_session

        def _tenant_not_found():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = None
            yield db

        app.dependency_overrides[get_session] = _tenant_not_found
        try:
            with TestClient(app) as c:
                resp = c.post(
                    "/api/v1/auth/token",
                    json={"tenant_id": "no-such-tenant", "secret": "x"},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides[get_session] = _no_db


class TestCampaignTrigger:
    """POST /campaigns/{id}/trigger response shape — spec: {run_id, message, 202}."""

    def test_trigger_returns_run_id(self, app) -> None:
        from zer0.db.session import get_session

        def _found_campaign():
            db = MagicMock()
            campaign = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = campaign
            yield db

        app.dependency_overrides[get_session] = _found_campaign
        try:
            # Patch the runner_service so no actual thread-pool work runs
            with patch("zer0.graph.runner_service.submit"):
                with TestClient(app) as c:
                    resp = c.post(
                        "/api/v1/campaigns/some-id/trigger",
                        headers={"X-Tenant-ID": "t1"},
                    )
            data = resp.json().get("data", {})
            assert "run_id" in data
            assert data.get("message") == "Campaign run queued."
            assert resp.status_code == 202
        finally:
            app.dependency_overrides[get_session] = _no_db


class TestApprovalDecisionShape:
    """POST /approvals/leads and /approvals/messages use {decision, reason, body}."""

    def test_qualify_empty_body_returns_422(self, client) -> None:
        resp = client.post(
            "/api/v1/approvals/leads/lead-1/qualify",
            json={},
            headers={"X-Tenant-ID": "t1"},
        )
        assert resp.status_code == 422

    def test_qualify_invalid_decision_returns_422(self, client) -> None:
        resp = client.post(
            "/api/v1/approvals/leads/lead-1/qualify",
            json={"decision": "maybe"},
            headers={"X-Tenant-ID": "t1"},
        )
        assert resp.status_code == 422

    def test_message_empty_body_returns_422(self, client) -> None:
        resp = client.post(
            "/api/v1/approvals/messages/msg-1",
            json={},
            headers={"X-Tenant-ID": "t1"},
        )
        assert resp.status_code == 422


class TestLeadsEndpoints:
    """GET/GET-by-id/PATCH /leads — spec: spec/product/09-api.md § /leads."""

    # ------------------------------------------------------------------
    # GET /leads
    # ------------------------------------------------------------------

    def test_list_leads_returns_200_with_correct_shape(self, app) -> None:
        from datetime import datetime
        from decimal import Decimal

        from zer0.db.session import get_session

        _NOW = datetime(2026, 4, 22, 9, 0, 0)

        lead_mock = MagicMock()
        lead_mock.id = "lead-uuid-1"
        lead_mock.tenant_id = "t1"
        lead_mock.campaign_id = "camp-1"
        lead_mock.link_id = "link-1"
        lead_mock.stage = "prospect"
        lead_mock.company_name = "Test Corp"
        lead_mock.domain = "test.com"
        lead_mock.industry = "SaaS"
        lead_mock.headcount_range = "50-200"
        lead_mock.business_type = "B2B"
        lead_mock.research_summary = "Summary text."
        lead_mock.signals = ["hiring"]
        lead_mock.score = Decimal("72.5")
        lead_mock.per_criterion_scores = []
        lead_mock.rationale = "Good fit."
        lead_mock.rejection_reason = None
        lead_mock.detected_language = "en"
        lead_mock.blocked_at = None
        lead_mock.created_at = _NOW
        lead_mock.updated_at = _NOW

        def _db_with_lead():
            db = MagicMock()
            db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                lead_mock
            ]
            # Simpler chain used by list_leads when only tenant_id filter is applied
            db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                lead_mock
            ]
            yield db

        app.dependency_overrides[get_session] = _db_with_lead
        try:
            with TestClient(app) as c:
                resp = c.get(
                    "/api/v1/leads",
                    headers={"X-Tenant-ID": "t1"},
                )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert "items" in data
            assert "next_cursor" in data
            items = data["items"]
            assert len(items) == 1
            item = items[0]
            # Current fields present
            assert item["id"] == "lead-uuid-1"
            assert item["company_name"] == "Test Corp"
            assert item["domain"] == "test.com"
            assert item["stage"] == "prospect"
            assert item["signals"] == ["hiring"]
            # Stale fields absent
            assert "name" not in item
            assert "company" not in item
            assert "url" not in item
            assert "source" not in item
            assert "contact_email" not in item
        finally:
            app.dependency_overrides[get_session] = _no_db

    def test_list_leads_without_tenant_header_returns_422(self, client) -> None:
        resp = client.get("/api/v1/leads")
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # GET /leads/{id}
    # ------------------------------------------------------------------

    def test_get_lead_not_found_returns_404(self, app) -> None:
        from zer0.db.session import get_session

        def _no_lead():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = None
            yield db

        app.dependency_overrides[get_session] = _no_lead
        try:
            with TestClient(app) as c:
                resp = c.get(
                    "/api/v1/leads/non-existent-id",
                    headers={"X-Tenant-ID": "t1"},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides[get_session] = _no_db

    # ------------------------------------------------------------------
    # PATCH /leads/{id}
    # ------------------------------------------------------------------

    def test_patch_lead_stage_returns_updated_lead(self, app) -> None:
        from datetime import datetime
        from decimal import Decimal

        from zer0.db.session import get_session

        _NOW = datetime(2026, 4, 22, 9, 0, 0)

        lead_mock = MagicMock()
        lead_mock.id = "lead-uuid-2"
        lead_mock.tenant_id = "t1"
        lead_mock.campaign_id = "camp-1"
        lead_mock.link_id = None
        lead_mock.stage = "prospect"
        lead_mock.company_name = "Patch Corp"
        lead_mock.domain = None
        lead_mock.industry = None
        lead_mock.headcount_range = None
        lead_mock.business_type = None
        lead_mock.research_summary = None
        lead_mock.signals = None
        lead_mock.score = None
        lead_mock.per_criterion_scores = None
        lead_mock.rationale = None
        lead_mock.rejection_reason = None
        lead_mock.detected_language = None
        lead_mock.blocked_at = None
        lead_mock.created_at = _NOW
        lead_mock.updated_at = _NOW

        def _db_with_lead():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = lead_mock
            yield db

        app.dependency_overrides[get_session] = _db_with_lead
        try:
            with TestClient(app) as c:
                resp = c.patch(
                    "/api/v1/leads/lead-uuid-2",
                    json={"stage": "qualified"},
                    headers={"X-Tenant-ID": "t1"},
                )
            assert resp.status_code == 200
        finally:
            app.dependency_overrides[get_session] = _no_db

    def test_patch_lead_not_found_returns_404(self, app) -> None:
        from zer0.db.session import get_session

        def _no_lead():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = None
            yield db

        app.dependency_overrides[get_session] = _no_lead
        try:
            with TestClient(app) as c:
                resp = c.patch(
                    "/api/v1/leads/missing",
                    json={"stage": "qualified"},
                    headers={"X-Tenant-ID": "t1"},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides[get_session] = _no_db

    def test_patch_lead_with_stale_contact_email_returns_422(self, client) -> None:
        """contact_email is no longer a valid PATCH field — must be rejected."""
        resp = client.patch(
            "/api/v1/leads/some-id",
            json={"contact_email": "hacker@example.com"},
            headers={"X-Tenant-ID": "t1"},
        )
        assert resp.status_code == 422

