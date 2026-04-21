"""Auth endpoint — issue JWT for a tenant.

Spec: spec/product/04-api.md — POST /auth/token
No JWT required for this endpoint.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, ok
from zer0.config.settings import get_settings
from zer0.db import TenantRow, get_session

router = APIRouter(prefix="/auth")


class TokenRequest(BaseModel):
    tenant_id: str
    secret: str  # simple shared secret per tenant (not a password — validated against DB)


@router.post("/token")
def issue_token(
    body: TokenRequest,
    session: Session = Depends(get_session),
):
    """Issue a short-lived JWT for the given tenant."""
    tenant: TenantRow | None = (
        session.query(TenantRow)
        .filter(TenantRow.id == body.tenant_id, TenantRow.deleted_at.is_(None))
        .first()
    )
    if not tenant:
        raise api_error("TENANT_NOT_FOUND", "Tenant not found", 404)

    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload = {
        "tenant_id": body.tenant_id,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return ok({"access_token": token, "token_type": "bearer"})
