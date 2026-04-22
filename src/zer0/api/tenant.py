"""Tenant endpoints.

Spec: spec/product/09-api.md
  POST   /tenants          — create a new tenant (no X-Tenant-ID required)
  GET    /tenant           — get current tenant settings
  PATCH  /tenant           — update current tenant settings
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from zer0.api._common import api_error, get_current_tenant_id, ok
from zer0.db import TenantRow, get_session

# Plural router — unauthenticated tenant bootstrap endpoints.
# Spec: spec/product/09-api.md §Auth: "every route except GET /health and POST /auth/token
# requires JWT" — TODO: enforce once Google OAuth login is implemented (spec phase 2).
tenants_router = APIRouter(prefix="/tenants")

# Singular router — operations on an existing tenant (requires X-Tenant-ID)
router = APIRouter(prefix="/tenant")


class TenantCreate(BaseModel):
    name: str


@tenants_router.get("")
def list_tenants(session: Session = Depends(get_session)):
    rows = (
        session.query(TenantRow)
        .filter(TenantRow.deleted_at.is_(None))
        .order_by(TenantRow.created_at)
        .all()
    )
    return ok([TenantOut(id=t.id, name=t.name, retargeting_cooldown_days=t.retargeting_cooldown_days, default_approval_mode=t.default_approval_mode) for t in rows])


@tenants_router.post("")
def create_tenant(
    body: TenantCreate,
    session: Session = Depends(get_session),
):
    if not body.name.strip():
        raise api_error("VALIDATION_ERROR", "name is required", 422)
    t = TenantRow(id=str(uuid.uuid4()), name=body.name.strip())
    session.add(t)
    session.commit()
    session.refresh(t)
    return ok(TenantOut(id=t.id, name=t.name, retargeting_cooldown_days=t.retargeting_cooldown_days, default_approval_mode=t.default_approval_mode))


class TenantOut(BaseModel):
    id: str
    name: str
    retargeting_cooldown_days: int
    default_approval_mode: str


class TenantPatch(BaseModel):
    name: str | None = None
    retargeting_cooldown_days: int | None = None
    default_approval_mode: str | None = None


def _get_tenant(tenant_id: str, session: Session) -> TenantRow:
    t = session.query(TenantRow).filter(TenantRow.id == tenant_id, TenantRow.deleted_at.is_(None)).first()
    if not t:
        raise api_error("TENANT_NOT_FOUND", "Tenant not found", 404)
    return t


@router.get("")
def get_tenant(
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    t = _get_tenant(tenant_id, session)
    return ok(TenantOut(id=t.id, name=t.name, retargeting_cooldown_days=t.retargeting_cooldown_days, default_approval_mode=t.default_approval_mode))


@router.patch("")
def patch_tenant(
    body: TenantPatch,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_session),
):
    t = _get_tenant(tenant_id, session)
    if body.name is not None:
        t.name = body.name
    if body.retargeting_cooldown_days is not None:
        t.retargeting_cooldown_days = body.retargeting_cooldown_days
    if body.default_approval_mode is not None:
        t.default_approval_mode = body.default_approval_mode
    session.add(t)
    return ok(TenantOut(id=t.id, name=t.name, retargeting_cooldown_days=t.retargeting_cooldown_days, default_approval_mode=t.default_approval_mode))
