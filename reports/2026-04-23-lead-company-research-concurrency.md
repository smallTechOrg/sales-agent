# Plan: Lead↔Company linkage, Web-search company enrichment, Research concurrency

**Date:** 2026-04-23
**Status:** PENDING APPROVAL
**Author:** planner
**Branch:** feat/cumulative-data

---

## 1. Goal

Three connected improvements to the post-identify pipeline so that:

1. Every identified lead is reliably surfaced as a `Company` in the dashboard (companies view shows the full universe of identified entities, tenant-scoped).
2. The research phase actively web-searches the lead's company and persists richer fields (website/domain confirmation, description, headcount estimate, business type, signals) onto the tenant-wide `CompanyRow` — not just onto the campaign-scoped `LeadRow`.
3. Research is parallelised across leads with a configurable concurrency, mirroring the recently parallelised `node_scrape_links`, so research stops being the run bottleneck.

These three are bundled because they share a single touchpoint: `node_research` writing to both `LeadRow` and `CompanyRow` under fan-out workers.

---

## 2. Spec impact

### 2a. `spec/product/07-data-model.md`

**`companies` table — extend with research fields**

The schema already lists `industry`, `headcount_range`, `business_type`, `research_summary`, `signals`. Add the following columns explicitly to the canonical schema (already implicit in the spec but missing as columns):

- `website` (TEXT) — canonical company website URL discovered during research (often equals `domain`, but kept separately because `domain` is the upsert key).
- `description` (TEXT) — short one-paragraph "what the company does" string from the research synthesis. Distinct from the cumulative `research_summary` log.
- `last_enriched_at` already exists — keep semantics: updated whenever `node_research` writes.

Write rule for these new fields: **fill-if-null** by the agent (consistent with existing `company_name`, `industry` rule). Never overwrite human-edited values.

**Indexes:** no new indexes.

### 2b. `spec/product/04-capabilities/02-enrichment.md`

Sub-step 3C ("Cumulative write") is updated:

- The synthesis prompt now produces, in addition to `company_summary` and `recent_signals`:
  - `description` (str) — one-paragraph "what the company does".
  - `website` (str | None) — canonical company URL.
  - `headcount_range` (str | None) — best-effort size estimate.
  - `business_type` (str | None) — `enterprise|mid_market|smb|...`.
- `node_research` writes these new fields to `CompanyRow` using fill-if-null semantics. `LeadRow` continues to receive only the existing fields.
- A new "Concurrency" subsection: research runs N leads in parallel via a `ThreadPoolExecutor`, controlled by `DiscoveryConfig.research_concurrency` (default 1, range 1–32). DB writes happen on the main thread, mirroring `node_scrape_links`.

### 2c. `spec/product/05-config.md`

Add `DiscoveryConfig.research_concurrency: int = 1` (range 1–32). Document alongside `scrape_concurrency`.

### 2d. `spec/product/02-architecture.md` and `spec/product/10-agent-graph.md`

Reaffirm tenancy invariant: `Company` is tenant-scoped (already true; one row per `(tenant_id, domain)`); `Lead` is campaign-scoped; `lead.company_id` is the join. Add a note in `node_identify_leads` and `node_research` describing the upsert/fill-if-null contract.

### 2e. `spec/product/09-api.md` and `spec/product/11-ui-dashboard.md`

- `GET /api/v1/companies` — extend `CompanyOut` with `website`, `description`, and a `lead_ids: list[str]` (or `lead_count: int`) so the UI can show the campaigns/leads each company surfaced in.
- `GET /api/v1/companies/{id}` — already returns `source_links`; add `leads` list (id, campaign_id, stage) so the company detail view links back to the leads.
- UI dashboard spec: confirm that the Companies screen lists every `CompanyRow` for the tenant — no campaign filter — and links each row to its underlying leads.

---

## 3. Engineering impact

None of the rules in `spec/engineering/` change. The concurrency pattern matches the precedent set by `node_scrape_links` (commit 66b7203) — `ThreadPoolExecutor`, per-worker LLM call, DB writes serialised on the main thread.

---

## 4. Phases

Each phase is gated by a verifiable test.

### Phase 1 — Domain + config (`domain/`, `config/`)

- Add `research_concurrency` to `DiscoveryConfig` (default 1, range 1–32).
- Extend the synthesis output type returned by `enrich_lead` to include optional `description`, `website`, `headcount_range`, `business_type`.
- **Gate:** unit tests for `DiscoveryConfig` validation; unit test for `enrich_lead` output schema.

### Phase 2 — DB schema (`db/`, alembic)

- Alembic migration adds `companies.website` and `companies.description` (both nullable TEXT).
- Update `CompanyRow` ORM model.
- **Gate:** migration `upgrade` + `downgrade` runs cleanly against a test DB; ORM round-trip test.

### Phase 3 — Tools (`tools/enrich_lead.py`, `prompts/researcher.md`)

- Update `prompts/researcher.md` to ask the LLM for `description`, `website`, `headcount_range`, `business_type` in the JSON output.
- Update `enrich_lead` to parse these fields and return them on the result object.
- **Gate:** unit test for `enrich_lead` parse path with a fixture LLM response.

### Phase 4 — Graph (`graph/nodes.py`)

- Refactor `node_research` to extract a `_research_one_lead(lead, llm, settings, ...) -> tuple[Lead, dict]` worker (no DB writes inside the worker).
- Drive workers through `ThreadPoolExecutor(max_workers=config.discovery_config.research_concurrency)`.
- After workers complete, on the main thread: write to `LeadRow`, fill-if-null on `CompanyRow` for `website`, `description`, `headcount_range`, `business_type`; append `research_summary` and dedup `signals`; bump `last_enriched_at`; emit `lead.researched` event.
- Confirm `node_identify_leads` already upserts `CompanyRow` for every lead (it does — see lines 414–445). No change needed there.
- **Gate:** integration test exercising `node_research` over multiple leads with concurrency > 1, asserting all `CompanyRow` rows receive new fields and `LeadRow.stage = research`.

### Phase 5 — API (`api/companies.py`, `api/leads.py`)

- Extend `CompanyOut` with `website`, `description`, and add either `lead_count` (cheap) or a list of `{id, campaign_id, stage}` leads on the detail endpoint.
- Verify `GET /companies` returns every `CompanyRow` for the tenant (it currently does — sanity check there is no hidden filter).
- **Gate:** API tests covering list + detail with newly identified-via-lead companies present.

### Phase 6 — UI (`web-scraper/`)

- Companies list page surfaces the new fields (`website`, `description`, `lead_count`).
- Company detail page shows associated leads with links into the lead pipeline view.
- **Gate:** UI smoke test (manual) plus existing component tests still pass.

### Phase 7 — Docs

- Update `README.md` if any CLI/config field surface visibly changes (it shouldn't — `research_concurrency` is a config field, not a CLI command).
- Update relevant spec files per §2.

---

## 5. Out of scope

- Changing the company upsert key away from `(tenant_id, domain)`.
- Re-running research on already-researched leads (current `stage in {prospect, research}` gating stays).
- Adding LinkedIn / Apollo / Clearbit-style enrichment providers — research stays "web search + scrape + LLM synthesis".
- Cross-tenant company knowledge sharing.
- Backfilling `website`/`description` for already-researched companies (operator can re-run; not part of this plan).
- Parallelising `qualify`, `get_people`, or `outreach` — only `research` in this plan.

---

## 6. Risks

| Risk | Detection |
| --- | --- |
| Concurrency causes DB session contention or deadlocks | Integration test in Phase 4 with concurrency=8; observe no `OperationalError`. DB writes are already serialised on the main thread, mirroring `scrape_links`. |
| LLM returns malformed JSON for the new fields | `enrich_lead` parser falls back to `None` per field; existing `enrichment_parse_error` failure mode applies. |
| Fill-if-null clobbers human-edited values | Explicitly check `is None` before assignment; covered by Phase 4 test fixture that pre-seeds a human value. |
| Companies surfaced via lead identification not appearing in UI is actually a UI filter bug, not an API bug | Phase 5 gate explicitly asserts API correctness; if the bug is UI-side, Phase 6 is where it lands. Tracked separately if API turns out fine. |
| Tavily quota exhausted under high research concurrency | Concurrency default stays 1; operator opts in. DDG fallback path remains. |
| `node_identify_leads` not always populating `lead.company_id` (nullable column) | Phase 4 test should assert `LeadRow.company_id IS NOT NULL` after identify for any lead with a domain; backfill query if needed. |

---

## 7. Open questions for the user

1. On the Companies API list endpoint, do you prefer `lead_count: int` (cheap) or a full `leads: [{id, campaign_id, stage}]` list (richer but heavier)?
2. Should `node_research` re-enrich a `CompanyRow` when a *new* lead surfaces for an already-researched company in a different campaign, or skip if `last_enriched_at` is recent (and how recent — 30 days)?
3. Default value for `research_concurrency` — keep at 1 (safe) or bump to match `scrape_concurrency` typical setting?
