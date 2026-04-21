"""Health endpoint — no auth required.

Spec: spec/product/09-api.md — GET /health
"""

from fastapi import APIRouter

from zer0.api._common import ok

router = APIRouter()


@router.get("/health")
def health():
    return ok({"status": "ok"})
