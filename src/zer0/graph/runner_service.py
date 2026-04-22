"""Runner service — non-blocking campaign execution.

Spec: spec/product/09-api.md — Threading model
Spec: spec/product/07-data-model.md — campaign_runs table

Agent runs execute in a dedicated ThreadPoolExecutor so uvicorn worker threads
are never blocked. Run lifecycle is tracked in the campaign_runs table so the
API can report status and current node without polling the agent state directly.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import structlog

from zer0.db.models import CampaignRunRow
from zer0.db.session import create_db_session

log = structlog.get_logger(__name__)

_MAX_WORKERS = int(os.getenv("ZER0_RUNNER_MAX_WORKERS", "4"))
_executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS, thread_name_prefix="zer0-runner")


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _update_run(run_id: str, **kwargs: object) -> None:
    """Update campaign_runs row with arbitrary fields. Swallows DB errors."""
    try:
        with create_db_session() as session:
            row = session.query(CampaignRunRow).filter(CampaignRunRow.id == run_id).first()
            if row:
                for k, v in kwargs.items():
                    setattr(row, k, v)
    except Exception as exc:
        log.warning("runner_service.update_run_failed", run_id=run_id, error=str(exc))


def _run_in_thread(
    *,
    run_id: str,
    campaign_id: str,
    tenant_id: str,
) -> None:
    """Execute the agent graph. Called inside the thread pool."""
    _update_run(run_id, status="running", started_at=_now(), current_node="resolve_config")
    try:
        from zer0.graph.runner import run_campaign
        run_campaign(campaign_id=campaign_id, tenant_id=tenant_id, run_id=run_id)
        _update_run(run_id, status="completed", finished_at=_now(), current_node=None)
    except Exception as exc:
        log.error("runner_service.run_failed", run_id=run_id, campaign_id=campaign_id, error=str(exc))
        _update_run(run_id, status="failed", finished_at=_now(), error=str(exc), current_node=None)


def recover_orphaned_runs() -> int:
    """Mark any runs stuck in pending/running as interrupted.

    Call once at application startup so the submit guard never blocks a fresh
    server from accepting new runs that belong to a previous process.
    """
    try:
        with create_db_session() as session:
            rows = (
                session.query(CampaignRunRow)
                .filter(CampaignRunRow.status.in_(["pending", "running"]))
                .all()
            )
            for row in rows:
                row.status = "interrupted"
                row.finished_at = _now()
                row.error = "Server restarted; run was interrupted and did not complete."
            count = len(rows)
        if count:
            log.warning("runner_service.orphaned_runs_recovered", count=count)
        return count
    except Exception as exc:
        log.error("runner_service.recover_orphaned_failed", error=str(exc))
        return 0


def submit(*, campaign_id: str, tenant_id: str, run_id: str) -> None:
    """Create a campaign_runs row and submit the run to the thread pool.

    Returns immediately. The caller gets status via GET /campaigns/{id}/runs/{run_id}.
    Raises RuntimeError if a run is already active for this campaign.
    """
    # Guard: reject if a run is already 'pending' or 'running' for this campaign
    try:
        with create_db_session() as session:
            active = (
                session.query(CampaignRunRow)
                .filter(
                    CampaignRunRow.campaign_id == campaign_id,
                    CampaignRunRow.tenant_id == tenant_id,
                    CampaignRunRow.status.in_(["pending", "running"]),
                )
                .first()
            )
            if active:
                raise RuntimeError(f"Run {active.id} is already {active.status} for campaign {campaign_id}")

            row = CampaignRunRow(
                id=run_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                status="pending",
            )
            session.add(row)
    except RuntimeError:
        raise
    except Exception as exc:
        log.error("runner_service.create_run_row_failed", run_id=run_id, error=str(exc))
        raise

    _executor.submit(
        _run_in_thread,
        run_id=run_id,
        campaign_id=campaign_id,
        tenant_id=tenant_id,
    )
    log.info("runner_service.submitted", run_id=run_id, campaign_id=campaign_id)
