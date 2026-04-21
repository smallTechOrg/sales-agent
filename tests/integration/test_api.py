# Phase-8 gate — API integration tests
# Spec: spec/engineering/phases.md § Phase 8
from __future__ import annotations

from unittest.mock import MagicMock

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

    def test_body_is_ok(self, client) -> None:
        assert client.get("/api/v1/health").json() == {"status": "ok"}


class TestAuthTokenFormat:
    """Validates request-body schema enforcement — no DB required."""

    def test_empty_body_returns_422(self, client) -> None:
        resp = client.post("/api/v1/auth/token", json={})
        assert resp.status_code == 422

    def test_missing_secret_field_returns_422(self, client) -> None:
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
