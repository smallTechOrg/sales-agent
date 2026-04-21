"""Shared API utilities — envelope, pagination, auth dependency.

Spec: spec/product/04-api.md — General conventions
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from zer0.config.settings import get_settings

_bearer = HTTPBearer()


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
# JWT auth dependency
# ---------------------------------------------------------------------------

def get_current_tenant_id(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Decode JWT and return tenant_id claim. Raises 401 on any failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        tenant_id: str = payload.get("tenant_id", "")
        if not tenant_id:
            raise ValueError("missing tenant_id claim")
        return tenant_id
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"data": None, "error": {"code": "UNAUTHORIZED", "message": str(exc)}},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
