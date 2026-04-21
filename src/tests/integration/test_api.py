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
            # Patch the background task runner so no actual graph runs
            with patch("zer0.graph.runner.run_campaign"):
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

