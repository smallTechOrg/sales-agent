"""Structured logging, Slack event posting, and audit trail writing.

Spec: spec/product/02-architecture.md — Module responsibilities / observability/
Spec: spec/product/02-architecture.md — Observability

Every tool call must call write_event() before returning. No silent actions.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
import structlog

from zer0.domain.config import ResolvedConfig

_log = structlog.get_logger(__name__)


def configure_logging(log_level: str = "INFO") -> None:
    """Call once at application startup."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def write_event(
    *,
    db: Any = None,  # sqlalchemy Session — optional; if None, logs only
    event_type: str,
    payload: dict[str, Any] | None = None,
    tenant_id: str,
    campaign_id: str | None = None,
    lead_id: str | None = None,
    person_id: str | None = None,
    config_snapshot: ResolvedConfig | None = None,
) -> None:
    """Write an event row to the audit log and emit a structured log entry.

    Spec: spec/product/03-db-schema.md — events table
    If db is None the event is logged only (no DB write).
    """
    _log.info(
        event_type,
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        lead_id=lead_id,
    )

    if db is None:
        return

    from zer0.db.models import EventRow  # local import — avoids circular deps

    import uuid

    row = EventRow(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        lead_id=lead_id,
        person_id=person_id,
        event_type=event_type,
        payload=payload or {},
        config_snapshot=config_snapshot.model_dump() if config_snapshot else None,
    )
    db.add(row)
    db.flush()


def post_slack_event(
    *,
    webhook_url: str,
    event_type: str,
    text: str,
    tenant_id: str,
) -> None:
    """Post a structured event notification to the tenant's Slack webhook.

    Spec: spec/product/02-architecture.md — Observability
    Fires-and-forgets. Failure is logged but never raises — Slack is best-effort.
    """
    try:
        resp = httpx.post(
            webhook_url,
            json={"text": f"[{event_type}] {text}"},
            timeout=5.0,
        )
        resp.raise_for_status()
    except Exception as exc:
        _log.warning(
            "slack_post_failed",
            event_type=event_type,
            tenant_id=tenant_id,
            error=str(exc),
        )
