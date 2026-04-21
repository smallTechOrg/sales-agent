"""FastAPI application factory.

Spec: spec/product/04-api.md
"""

from __future__ import annotations

from fastapi import FastAPI

from zer0.api.approvals import router as approvals_router
from zer0.api.auth import router as auth_router
from zer0.api.campaigns import router as campaigns_router
from zer0.api.events import router as events_router
from zer0.api.health import router as health_router
from zer0.api.leads import router as leads_router
from zer0.api.messages import router as messages_router
from zer0.api.offerings import router as offerings_router
from zer0.api.tenant import router as tenant_router
from zer0.api.tenant import tenants_router
from zer0.observability.events import configure_logging

_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Zer0 Sales Agent", version="0.1.0")

    app.include_router(health_router, prefix=_PREFIX)
    app.include_router(auth_router, prefix=_PREFIX)
    app.include_router(tenant_router, prefix=_PREFIX)
    app.include_router(tenants_router, prefix=_PREFIX)
    app.include_router(offerings_router, prefix=_PREFIX)
    app.include_router(campaigns_router, prefix=_PREFIX)
    app.include_router(leads_router, prefix=_PREFIX)
    app.include_router(approvals_router, prefix=_PREFIX)
    app.include_router(messages_router, prefix=_PREFIX)
    app.include_router(events_router, prefix=_PREFIX)

    return app


app = create_app()
