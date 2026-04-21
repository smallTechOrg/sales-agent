"""Auth endpoint — issue JWT for a tenant.

Spec: spec/product/09-api.md — POST /auth/token
No JWT required for this endpoint.

NOTE: Google OAuth (as specced) is deferred. For now a simple shared-secret
per-tenant is used so the operator can log in without a Google app setup.
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
    secret: str  # shared secret validated against tenant.auth_secret_hash (plain for now)


@router.post("/token")
def issue_token(
    body: TokenRequest,
    session: Session = Depends(get_session),
):
    """Issue a short-lived JWT for the given tenant.

    The secret is compared against the stored value in plain text for now.
    Swap for bcrypt verify when hardening for production.
    """
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
        "sub": body.tenant_id,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    expires_at = (now + timedelta(hours=8)).isoformat()
    return ok({"access_token": token, "expires_at": expires_at})


