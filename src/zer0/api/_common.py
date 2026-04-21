"""Shared API utilities — envelope, pagination, auth dependency.

Spec: spec/product/04-api.md — General conventions
"""

from __future__ import annotations

from typing import Any

from fastapi import Header, HTTPException, status
from pydantic import BaseModel


class OKResponse(BaseModel):
    data: Any
    error: None = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    data: None = None
    error: ErrorDetail


class PaginatedData(BaseModel):
    items: list[Any]
    next_cursor: str | None


def ok(data: Any) -> dict:
    return {"data": data, "error": None}


def paginated(items: list, next_cursor: str | None) -> dict:
    return {"data": {"items": items, "next_cursor": next_cursor}, "error": None}


def api_error(code: str, message: str, status_code: int = 400) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"data": None, "error": {"code": code, "message": message}},
    )


# ---------------------------------------------------------------------------
# Tenant identity dependency — no auth for now, operator uses UI directly
# ---------------------------------------------------------------------------

def get_current_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract tenant identity from the X-Tenant-ID request header."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"data": None, "error": {"code": "MISSING_TENANT", "message": "X-Tenant-ID header is required"}},
        )
    return x_tenant_id
