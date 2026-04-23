# Plan — LLM cost tracking + source links & page excerpts

**Date:** 2026-04-23
**Branch:** feat/cumulative-data
**Author:** planner (Claude Code)

---

## 1. Goal

Two additions to surface more operator-visible state during and after a campaign run:

1. **LLM cost tracking** — capture Gemini token usage on every LLM call, accumulate it
   onto the active `campaign_run`, and render input/output/cost on the campaign runs list.
2. **Source links + page excerpts** — on the lead detail and company detail pages, show
   the source URL(s) (with source badge) and a short, safe-to-return page excerpt
   derived from `links.page_text`.

Includes a full spec-vs-code drift pass so the committed state is consistent.

---

## 2. Spec impact

### `spec/product/07-data-model.md`

- **`links` table** — add column:
  - `page_excerpt TEXT` — first ~500 chars of scraped body, HTML-stripped. **Safe to
    return in API responses.** `page_text` remains never-returned. Populated at scrape
    time by the fetch tool.
- **`campaign_runs` table** — add columns:
  - `input_tokens INTEGER NOT NULL DEFAULT 0`
  - `output_tokens INTEGER NOT NULL DEFAULT 0`
  - `total_tokens INTEGER NOT NULL DEFAULT 0`
  - `llm_call_count INTEGER NOT NULL DEFAULT 0`
  - `estimated_cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0`
  - Accumulated by the runner for the duration of the run. Model pricing lives in a
    small in-code table keyed by model name (`gemini-2.0-flash`, etc.).

### `spec/product/09-api.md`

- **Link object shape** — add `"page_excerpt": "<string | null>"`. Reiterate that
  `page_text` is never returned.
- **Campaign-run object shape** (`GET /campaigns/{id}/runs`, `GET .../runs/{run_id}`) —
  document the shape and add the five cost/token fields. The endpoint is referenced in
  the resource map but has no response shape section yet; add one.

### `spec/product/11-ui-dashboard.md`

- **Campaign detail / runs list** — add a "Cost" column group (input / output / total
  tokens, `$0.0000` estimated cost) per run row.
- **Lead detail → Profile section** — add a "Source" subsection:
  sources badge + linked URL for `lead.link_id`, plus a collapsible "Page excerpt"
  block showing `links.page_excerpt` (truncated display with "show more"
  expanding up to the full 500 chars).
- **Company detail → new "Source links" section** — table of all links from
  `link_leads` for this company, columns: URL, source badge, scraped_at, excerpt
  (expandable).

### `spec/product/02-architecture.md` — no change.
### `spec/product/10-agent-graph.md` — no change (token capture is cross-cutting at the
LLM layer, not a node-level contract).

---

## 3. Engineering impact

None. No `spec/engineering/` rule is affected. `secret-hygiene.md` is reinforced
(excerpt is explicitly the sanitized, API-safe projection of `page_text`).

---

## 4. Drift audit findings (to be fixed alongside this work)

Pre-existing drift noted while reading spec and code; these must land in the same
session so the tree is consistent:

1. `spec/product/07-data-model.md` contains a **duplicated trailing section** (old
   `offerings` / `campaigns` / `leads` / `messages` / `replies` / `events` definitions
   starting around line 580) from a prior edit. Delete the duplicated block; the
   canonical definitions are higher up.
2. `campaign_runs` spec is missing `run_status` enum values — spec references a
   `run_status` enum but the enum-types table does not list it. Add
   `run_status: pending, running, completed, failed`.
3. `tenants.enabled` column exists in ORM (`TenantRow.enabled`) but not in
   `07-data-model.md`. Add it (BOOLEAN, NOT NULL, DEFAULT true).
4. `people.full_name` and `people.linkedin_url` exist in ORM but not in spec. Add.
5. `leads.detected_language` present in both; fine. `leads` spec missing
   `company_id` ordering note — present already, acceptable.
6. `LinkRow.campaign_id` is nullable in ORM (per migration 0004); spec already
   reflects this but still lists `campaign_id` FK — confirm wording. OK.
7. `spec/product/11-ui-dashboard.md` screen map still references a `GET /api/v1/tenants`
   list endpoint that is not in `09-api.md`. Out of scope for this plan; note and
   leave alone unless trivial.

Fix items 1–5 in Phase 0.

---

## 5. Phases

### Phase 0 — Spec alignment & drift fixes
- Edit `spec/product/07-data-model.md`: delete duplicate trailing block, add
  `run_status` enum, add `tenants.enabled`, add `people.full_name` +
  `linkedin_url`, add `page_excerpt` on `links`, add token/cost columns on
  `campaign_runs`.
- Edit `spec/product/09-api.md`: add `page_excerpt` to link shape; add campaign-run
  object shape section with token/cost fields.
- Edit `spec/product/11-ui-dashboard.md`: add cost column to runs list, source
  subsection on lead detail, source-links section on company detail.
- **Gate:** markdown renders; `rg` confirms no lingering duplicate headings; link
  validation workflow clean.
- **Commit:** `phase-0: align specs for cost tracking + source excerpts`.

### Phase 1 — DB migration + ORM
- New Alembic migration `0008_cost_tracking_and_page_excerpt.py`:
  - `ALTER TABLE links ADD COLUMN page_excerpt TEXT`.
  - `ALTER TABLE campaign_runs ADD COLUMN input_tokens / output_tokens /
    total_tokens / llm_call_count / estimated_cost_usd` (with defaults).
- Update `src/zer0/db/models.py`: `LinkRow.page_excerpt`,
  `CampaignRunRow.input_tokens / output_tokens / total_tokens / llm_call_count /
  estimated_cost_usd`.
- **Gate:** `alembic upgrade head` on a fresh DB succeeds; downgrade works;
  existing unit tests under `src/tests/unit/db/` still green.
- **Commit:** `phase-5: add page_excerpt + run cost columns`.

### Phase 2 — Domain + LLM cost capture
- New dataclass `zer0.domain.llm_usage.LLMUsage` (input_tokens, output_tokens,
  total_tokens, model, cost_usd).
- Extend `LLMProvider.complete` return contract: return a tuple
  `(text, LLMUsage)` OR add a parallel `complete_with_usage()` — prefer the
  latter to avoid touching every caller in one phase. Existing `complete()`
  delegates to the new method and discards usage.
- `GeminiProvider.complete_with_usage`: read
  `response.usage_metadata.prompt_token_count` and `candidates_token_count`,
  compute cost via a small model-price table in `zer0/llm/pricing.py`.
- Thread-local / contextvar accumulator in `zer0/llm/usage_sink.py`:
  `current_run_id: ContextVar[str | None]`. When set, every
  `complete_with_usage` call appends usage to an in-memory aggregator keyed by
  run_id.
- **Gate:** new unit tests — `test_gemini_usage.py` (mocked SDK response),
  `test_usage_sink.py` (contextvar correctly scopes accumulation).
- **Commit:** `phase-4: capture Gemini token usage per call`.

### Phase 3 — Runner integration
- In `zer0/graph/runner.py` (or `runner_service.py`): at run start set
  `usage_sink.current_run_id`; at run end flush accumulated totals into the
  `campaign_runs` row (input_tokens, output_tokens, total_tokens,
  llm_call_count, estimated_cost_usd). Also flush periodically (every node
  completion) so mid-run polling shows non-zero values.
- **Gate:** integration test that runs a stubbed 2-LLM-call graph and asserts the
  `campaign_runs` row has the summed tokens/cost.
- **Commit:** `phase-7: accumulate token usage onto campaign_runs`.

### Phase 4 — Scraper page_excerpt
- Locate the scrape tool (`zer0/tools/` — scraping lives in `web-scraper` sibling
  repo but the link row is written here; identify the write site). When
  `page_text` is populated, also compute `page_excerpt = first 500 chars of
  BeautifulSoup-stripped text`.
- Backfill note: for rows created before the migration, `page_excerpt` is NULL;
  the API returns null; UI renders "No excerpt available". No data backfill job
  in v1.
- **Gate:** unit test asserting excerpt is ≤500 chars, contains no `<` `>` chars,
  preserves whitespace.
- **Commit:** `phase-6: populate page_excerpt at scrape time`.

### Phase 5 — API surface
- `GET /links` and `GET /links/{id}/leads`: include `page_excerpt` in link
  objects. Keep `page_text` filtered out.
- `GET /campaigns/{id}/runs` and `GET /campaigns/{id}/runs/{run_id}`: include
  `input_tokens`, `output_tokens`, `total_tokens`, `llm_call_count`,
  `estimated_cost_usd`.
- **Gate:** API unit tests for link shape + run shape.
- **Commit:** `phase-8: expose page_excerpt and run cost on API`.

### Phase 6 — UI
- `src/ui/src/app/[tenantId]/campaigns/[campaignId]/page.tsx`: add cost columns
  to the runs list. Format cost as `$0.0000`.
- Lead detail page: Source subsection with badge + URL + expandable page_excerpt.
- Company detail page: Source-links section (table of contributing links via
  `GET /companies/{id}/links` — reuse `link_leads`; if endpoint missing, add it
  in Phase 5).
- Update `src/ui/src/lib/api.ts` types for `Link.page_excerpt` and
  `CampaignRun.input_tokens / output_tokens / total_tokens / llm_call_count /
  estimated_cost_usd`.
- **Gate:** `npm run build` succeeds; lint/type-check clean.
- **Commit:** `phase-11: surface run cost and source excerpts in UI`.

### Phase 7 — Session end
- Run full test suite. `git status` clean. Session report updated. PR opened
  (or existing PR updated). README updated if any runnable component changed
  (none expected here).

---

## 6. Out of scope

- Backfilling `page_excerpt` for pre-existing `links` rows.
- Per-node cost breakdown (only whole-run totals in v1; node-level can be added
  later via events).
- Cost tracking for providers other than Gemini (future providers must populate
  `LLMUsage` themselves; the sink is provider-agnostic).
- Cost budgets / alerts / rate limits — display only for v1.
- Streaming responses (current SDK call is non-streaming).
- Editing `page_excerpt` — it is agent-written only.
- Any change to the agent graph topology.

---

## 7. Risks

- **Gemini SDK usage-metadata shape:** `google-genai>=1.0` exposes
  `response.usage_metadata` with `prompt_token_count`,
  `candidates_token_count`, `total_token_count`. If a call fails
  mid-generation, metadata may be missing — guard with `getattr(..., 0)` and
  still emit an `LLMUsage` with zeros.
- **ContextVar propagation into threads:** the runner uses a
  `ThreadPoolExecutor`. `ContextVar` values do **not** automatically
  propagate across `submit()` without `contextvars.copy_context().run(...)`.
  Runner must explicitly copy context when dispatching, or set the run_id at
  the top of the worker function. Verified by the Phase 3 integration test.
- **Pricing table drift:** Gemini prices change. Keep the table minimal
  (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) with a default
  fallback of 0 and a warning log when the current model is unpriced.
- **HTML stripping:** naive stripping may leave scripts/styles. Use
  BeautifulSoup `get_text(separator=" ", strip=True)` on already-fetched
  `page_text`; if `page_text` was stored post-stripping upstream, excerpt is
  trivially a slice.
- **Schema migration order:** must land before any code that reads/writes the
  new columns. Phase ordering (1 before 2/3/4) enforces this.
