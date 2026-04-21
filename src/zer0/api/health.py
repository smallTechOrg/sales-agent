"""Health endpoint — no auth required.

Spec: spec/product/04-api.md — GET /health
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
