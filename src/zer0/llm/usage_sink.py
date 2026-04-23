"""Per-run LLM usage accumulator.

Usage is accumulated in a thread-local dict keyed by run_id. The runner sets
current_run_id at the start of a run and calls flush_usage() at the end to
persist totals onto the campaign_runs row.

ContextVar semantics: values do NOT propagate automatically across
ThreadPoolExecutor.submit(). Callers that dispatch work into threads must
explicitly copy the context:

    ctx = contextvars.copy_context()
    executor.submit(ctx.run, worker_fn, *args)
"""

from __future__ import annotations

import threading
from contextvars import ContextVar
from dataclasses import dataclass, field

current_run_id: ContextVar[str | None] = ContextVar("current_run_id", default=None)

_lock = threading.Lock()
_accumulators: dict[str, "_RunUsage"] = {}


@dataclass
class _RunUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    llm_call_count: int = 0
    estimated_cost_usd: float = 0.0


def record(
    *,
    run_id: str | None,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
) -> None:
    """Record a single LLM call's usage. No-op if run_id is None."""
    if run_id is None:
        return
    with _lock:
        acc = _accumulators.setdefault(run_id, _RunUsage())
        acc.input_tokens += input_tokens
        acc.output_tokens += output_tokens
        acc.total_tokens += input_tokens + output_tokens
        acc.llm_call_count += 1
        acc.estimated_cost_usd += cost_usd


def get_usage(run_id: str) -> _RunUsage | None:
    with _lock:
        return _accumulators.get(run_id)


def clear_usage(run_id: str) -> _RunUsage | None:
    """Remove and return accumulated usage for a run (called after flush)."""
    with _lock:
        return _accumulators.pop(run_id, None)
