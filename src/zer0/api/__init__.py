"""FastAPI application factory.

Spec: spec/product/04-api.md
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zer0.api.approvals import router as approvals_router
from zer0.api.auth import router as auth_router
from zer0.api.campaigns import router as campaigns_router
from zer0.api.customers import router as customers_router
from zer0.api.events import router as events_router
from zer0.api.health import router as health_router
from zer0.api.leads import router as leads_router
from zer0.api.links import router as links_router
from zer0.api.messages import router as messages_router
from zer0.api.offerings import router as offerings_router
from zer0.api.tenant import router as tenant_router
from zer0.api.tenant import tenants_router
from zer0.config.settings import get_settings
from zer0.observability.events import configure_logging

_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Zer0 Sales Agent", version="0.1.0")

    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router, prefix=_PREFIX)
    app.include_router(auth_router, prefix=_PREFIX)
    app.include_router(tenant_router, prefix=_PREFIX)
    app.include_router(tenants_router, prefix=_PREFIX)
    app.include_router(offerings_router, prefix=_PREFIX)
    app.include_router(campaigns_router, prefix=_PREFIX)
    app.include_router(leads_router, prefix=_PREFIX)
    app.include_router(approvals_router, prefix=_PREFIX)
    app.include_router(messages_router, prefix=_PREFIX)
    app.include_router(links_router, prefix=_PREFIX)
    app.include_router(customers_router, prefix=_PREFIX)
    app.include_router(events_router, prefix=_PREFIX)

    return app


app = create_app()
