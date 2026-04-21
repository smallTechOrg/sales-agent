"""post_slack_event tool.

Spec: spec/product/02-architecture.md — Tools table
Thin wrapper that delegates to observability.post_slack_event.
Exposed as a tool so graph nodes can call it uniformly alongside all other tools.
"""

from __future__ import annotations

from zer0.observability.events import post_slack_event as _post_slack_event


def post_slack_event(
    *,
    webhook_url: str,
    event_type: str,
    tenant_id: str,
    payload: dict,
) -> None:
    """Post a Slack notification for the given event (best-effort, no retry)."""
    _post_slack_event(
        webhook_url=webhook_url,
        event_type=event_type,
        tenant_id=tenant_id,
        payload=payload,
    )
