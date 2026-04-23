# Plan: Configurable limits + parallelism for link scrape/analysis

**Date:** 2026-04-23
**Branch:** feat/cumulative-data
**Owner:** planner

## Goal

The `node_scrape_links` pipeline currently iterates every link in `AgentState.links`
sequentially, issuing one HTTP fetch + one LLM analysis call per link on the main
thread. Runs stall for long periods on slow/broken targets and do no useful work
in parallel. Add two knobs — a per-run cap on how many links get scraped/analysed
and a worker-pool for parallel execution — so an operator can trade cost for
latency without editing code.

## Spec impact

Spec edits travel in the same commit as the code that implements each phase.

### `spec/product/02-architecture.md`

- `DiscoveryConfig` table (Granular config models) gains two rows:
  - `max_links_per_run` — hard cap on the number of links fed into `scrape_links`
    per agent tick. Separate from `volume_per_run` (which caps discovery writes).
    If absent, defaults to `volume_per_run`.
  - `scrape_concurrency` — number of worker threads used by `node_scrape_links`
    for fetch + analysis. Default `1` (current behaviour).
- `Campaign` table (Configuration hierarchy): add `max_leads_per_run` — cap on
  how many identified leads a run will push past `node_identify_leads`. This is
  a campaign-level override; NULL means reuse `volume_cap`.

### `spec/product/05-config.md`

- Document the two new `DiscoveryConfig` fields under "Granular config models"
  section and note they are Campaign-overridable. No new `.env` vars.

### `spec/product/07-data-model.md`

- No table changes. Both new fields live inside the existing
  `offerings.discovery_config` and `campaigns.discovery_override` JSONB columns,
  so validation happens at Pydantic read time (no migration).
- `campaigns.volume_cap` remains the per-run lead cap; we add a new column only
  if we decide campaign-level lead cap is distinct from volume_cap. **Decision
  for this plan:** reuse existing `volume_cap` as `max_leads_per_run`; document
  that semantic in 07-data-model.md.

### `spec/product/04-capabilities/01-discovery.md`

- Clarify step 4: trim uses `min(volume_per_run, max_links_per_run)`.
- Add a new capability note referencing `scrape_concurrency` that governs the
  downstream `scrape_links` node (link only — full behaviour described in the
  scrape-links capability doc, which currently does not exist; out of scope to
  create here but note the gap).

## Engineering impact

None. No change to `ai-agents.md`, `tenant-isolation.md`, `code-style.md`.
Parallelism uses stdlib `concurrent.futures.ThreadPoolExecutor` — no new
dependency. DB writes inside workers must still go through `create_db_session()`
in a per-worker session; we will not share a Session across threads (SQLAlchemy
Sessions are not thread-safe).

## Phases

### Phase 1 — Domain model + config resolver

- Add `max_links_per_run: int | None` and `scrape_concurrency: int = 1` to
  `DiscoveryConfig` in `src/zer0/domain/config.py`.
- Bound `scrape_concurrency` with `Field(ge=1, le=32)` (safety cap).
- Update `ConfigResolver.resolve` merge in `src/zer0/config/resolver.py` if needed
  (fields are inside `discovery_config` JSONB, so automatic via Pydantic).
- **Gate:** unit tests for the new fields: default values, validation bounds,
  Campaign override merge over Offering default.

### Phase 2 — Apply `max_links_per_run` cap

- In `node_scrape_links` (`src/zer0/graph/nodes.py`), before iterating
  `state["links"]`, slice to `effective_max = disc.max_links_per_run or
  disc.volume_per_run`. Links beyond the cap are left untouched (scrape_status
  remains `pending`) so a future run can pick them up.
- Log `scrape_links.capped` event with the skipped count.
- **Gate:** unit test — feed 10 links with cap=3, assert only 3 scraped and 7
  remain `pending` in the returned state.

### Phase 3 — Parallel scrape + analysis workers

- Refactor the per-link body of `node_scrape_links` into a pure helper
  `_process_one_link(link, llm, tenant_id) -> (link_with_updates, db_updates)`
  that does NOT touch the DB.
- Wrap iteration in `ThreadPoolExecutor(max_workers=disc.scrape_concurrency)`.
  Submit one future per link; collect results as they complete.
- After the executor drains, perform DB writes on the main thread in a single
  `create_db_session()` block (batched by link id). This keeps Session use
  single-threaded.
- Preserve ordering of `updated` list to match input order (collect into a dict
  keyed by link.id, then emit in original order) so downstream nodes see a
  deterministic list.
- **Gate:**
  - unit test: concurrency=4 with 8 fake links, verify all 8 processed and DB
    writes invoked 8 times.
  - unit test: one worker raises — other 7 still complete; failing link marked
    `scrape_status=failed`.
  - timing smoke test (not CI-gated): concurrency=4 on 8 links with 100ms sleep
    per link finishes under 300ms vs ~800ms sequential.

### Phase 4 — Enforce `max_leads_per_run` cap downstream

- In `node_identify_leads`, read `state["config"].volume_cap` (existing field,
  re-documented as `max_leads_per_run`). After lead extraction, trim the output
  list to `volume_cap` if set.
- Emit `leads.capped` event with the skipped count. Links whose extracted leads
  are trimmed are NOT marked `identified_at`, so they can be retried.
- **Gate:** unit test — identify returns 10 leads with volume_cap=4, assert only
  4 leads returned and 6 links still eligible (`identified_at IS NULL`).

### Phase 5 — UI + API surface

- `src/zer0/api/offerings.py` + `src/zer0/api/campaigns.py`: the new fields are
  already serialised via the `DiscoveryConfig` Pydantic model — verify JSON
  responses and PATCH payloads accept them. No route changes expected.
- Next.js dashboard: add `max_links_per_run` and `scrape_concurrency` inputs to
  the Offering / Campaign edit form under the Discovery section. Re-use
  existing numeric input components. Tooltip copy explains the trade-off.
- **Gate:**
  - API contract test: PATCH offering with new fields → GET returns them.
  - UI Playwright (or manual): form saves + re-loads the new fields.

### Phase 6 — Docs + README

- Update README quick-start (if it describes discovery config) and
  `spec/product/02-architecture.md` Granular config models table.
- **Gate:** drift-auditor subagent run on the diff → no findings.

## Out of scope

- Rewriting `scrape_page` itself (using aiohttp / async). We stay with the
  existing sync `requests`-based tool; parallelism comes from threads.
- Making `node_identify_leads` parallel. LLM calls there are already per-link
  and we want to keep lead extraction deterministic for this change.
- A separate "scrape workers" process or queue (Celery/ARQ). v1 stays
  in-process; the architecture spec already names this as the future path.
- Adaptive concurrency / adaptive rate-limit detection. Fixed worker count only.
- Retrying `failed` links within the same run — retry continues to be "next
  run picks up pending/failed links", unchanged.

## Risks

| Risk | How we'll know | Mitigation |
|---|---|---|
| Thread-unsafe SQLAlchemy Session usage crashes a run | Unit test hitting DB from a worker; integration smoke run | Workers return data only; DB writes stay on main thread |
| LLM provider rate-limits under higher concurrency | `llm.rate_limited` warnings spike in `events` | Default `scrape_concurrency=1`; operator opts in |
| `max_links_per_run` hides links forever if always > cap | Links with `scrape_status=pending` pile up in DB | Add a dashboard query: count of pending links per campaign; not gated here but flagged |
| Re-entrancy — two concurrent runs scraping the same link | Duplicate LLM spend, race on `scrape_status` | Out of scope; `runner_service` already serialises runs per-campaign |
| Ordering-sensitive downstream nodes break when results arrive out of order | Test failures in `node_identify_leads` | Phase 3 preserves input order via dict-then-emit |
