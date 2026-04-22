# Plan: Cumulative Data, Research Fix, Company-Size Non-Blocking

**Date:** 2026-04-22  
**Status:** PENDING APPROVAL  
**Author:** planner

---

## 1. Goal

Make all pipeline data (links, customers, contacts) cumulative and tenant-scoped so knowledge persists and is shared across campaigns. Fix the research step so it actively web-searches the prospect company rather than summarising already-scraped page text. Remove company size as a rejection criterion.

---

## 2. Spec impact

### 2a. `spec/product/07-data-model.md`

**`links` table — lift campaign scope to tenant scope**

- Change unique constraint from `(tenant_id, campaign_id, url)` → `(tenant_id, url)`.
- Remove `campaign_id` FK from `links` as the deduplication key; keep it as a nullable attribute (`first_campaign_id`) for provenance.
- Add `lead_ids` view / junction table `link_leads` (`link_id`, `lead_id`, `tenant_id`) so we can query "what leads came from this link" and "what links contributed to this customer".
- `links.identified_at` semantics stay the same — NULL until identify step runs.

> Delta: update `links` table spec, add `link_leads` junction table and its indexes.

**`contacts` table — lift to customer scope**

- Change `contact.lead_id` → `contact.customer_id` so the same person at the same company is one row across all campaigns.
- Add `lead_contacts` junction table (`contact_id`, `lead_id`, `tenant_id`) to track in which campaigns a contact appears.
- Unique constraint moves from `(lead_id, email)` → `(customer_id, email)`.

> Delta: update `contacts` table spec, add `lead_contacts` junction table.

**`customers` table — add `source_link_ids` back-reference**

- No new column needed; the `link_leads` junction already provides the path: customer ← leads ← link_leads ← links.
- Document this query path explicitly in the customer spec section.

**`ICP.company_size_range` — mark optional / non-blocking**

- Add a note: "`company_size_range` is informational only. The qualification rubric MUST NOT include a company-size criterion that causes automatic rejection. If headcount is unknown, it is treated as `NULL` without penalising the lead."

### 2b. `spec/product/04-capabilities/01-discovery.md`

**Link dedup scope**

- Change deduplication rule from "URL unique per campaign" → "URL unique per tenant".
- On discovery, for a URL already stored for the tenant: skip `INSERT`, re-use the existing `LinkRow`. Record the current campaign in `link_leads`.
- Update "Outputs" table: `links` rows — upsert on `(tenant_id, url)`.

### 2c. `spec/product/04-capabilities/02-enrichment.md`

**Research step redesign (node_research)**

New three-sub-step description:

1. **Prospect identified** (input: `Lead` at stage `prospect` with `domain` + `company_name`). No LLM here — the identify step already produced these.

2. **Independent web research** (`node_research` sub-step A):
   - Call `web_search(query="{company_name} {domain} overview")` (Tavily + DuckDuckGo) to fetch 3–5 fresh pages about the company.
   - Scrape each returned URL via `scrape_page`.
   - Collect the scraped texts as `research_sources`.

3. **Synthesis** (`node_research` sub-step B):
   - Call `enrich_lead(lead, research_sources, config.icp)` — an LLM call that reads the freshly scraped research pages and produces `signals` + `research_summary`.
   - Cumulative append rules remain: new signals appended to `customer.signals`; new summary paragraph appended to `customer.research_summary`.
   - `lead.research_summary` and `lead.signals` continue to mirror `customer` (copied at write time for fast lead-level reads).

Remove the current description that implies `enrich_lead` operates solely on the discovery-page text.

Add to Inputs table: `web_search` tool + Tavily/DuckDuckGo config.

### 2d. `spec/product/04-capabilities/03-qualification.md`

**Company size non-blocking**

- Add rule: "The `company_size_range` field from `ICP` MUST NOT appear as a mandatory rubric criterion. If it is included in `rubric_criteria`, its weight must be zero or the criterion must have `required: false`."
- Add to "Out of scope": "Automatic rejection solely on the basis of unknown or mismatched company size."

### 2e. `spec/product/02-architecture.md`

**Domain model updates**

Update `Link` model entry: remove `campaign_id` from key fields; reference `link_leads`.  
Update `Contact` model entry: change `lead_id` → `customer_id` + reference `lead_contacts`.  
Update `ICP` model entry: mark `company_size_range` optional.  
Update tools table: `enrich_lead` — expand description to include web-search sourcing.

---

## 3. Engineering impact

No changes to engineering rules. The migration strategy (Alembic) is already specified. The tool-layer split (web_search called by graph nodes, not each other) is already the correct pattern per architecture rules.

---

## 4. Phases

### Phase 1 — Spec updates (no code)
Update the five spec files listed in §2.  
**Gate:** no gate — spec is reviewed by the user before Phase 2 starts.

### Phase 2 — Schema migration
- Alembic migration: remove `campaign_id` from `links` unique constraint; add `(tenant_id, url)` unique; add `link_leads` junction table; add `lead_contacts` junction table; change `contacts.lead_id` → `contacts.customer_id`.
- Update ORM models in `src/zer0/db/models.py` to match.  
**Gate:** `alembic upgrade head` runs clean in a fresh DB; existing data migration script does not violate tenant isolation (verified by unit test with fixture data).

### Phase 3 — Domain model updates
- Update Pydantic models in `src/zer0/domain/`: `Link`, `Contact`, `ICP` (make `company_size_range` optional), `Customer`.
- Update repository layer: `LinkRepository.upsert` uses `(tenant_id, url)` key; `ContactRepository.upsert` uses `(customer_id, email)` key.  
**Gate:** unit tests for `LinkRepository.upsert` and `ContactRepository.upsert` pass; no `campaign_id` in link upsert path.

### Phase 4 — Research node redesign
- Refactor `node_research` / `enrich_lead` tool to:
  1. Call `web_search` with company name + domain as query.
  2. Scrape returned results via `scrape_page`.
  3. Pass scraped texts to LLM (`enrich_lead`) for synthesis.
- Update `prompts/researcher.md` to accept `research_sources` (list of scraped texts) as input variable.  
**Gate:** unit test for `enrich_lead` mocks `web_search` + `scrape_page` and verifies the prompt rendered to the LLM includes research source text, not just existing lead fields.

### Phase 5 — Discovery node: tenant-scoped link dedup
- Update `node_discover` to deduplicate by `(tenant_id, url)` instead of `(tenant_id, campaign_id, url)`.
- On URL already seen: skip insert; write to `link_leads` junction instead.  
**Gate:** unit test: same URL provided by two campaigns → one `links` row, two `link_leads` rows.

### Phase 6 — Contact dedup across campaigns
- Update `node_get_contacts` to upsert contacts on `(customer_id, email)`.
- Write to `lead_contacts` junction when a contact re-appears in a new campaign.  
**Gate:** unit test: same contact email found in two campaigns → one `contacts` row, two `lead_contacts` rows.

### Phase 7 — Qualification: remove company-size rejection path
- Ensure `qualify_lead` tool does not fail or reject solely on `headcount_range = NULL`.
- If `ICP.company_size_range` is `None`, skip that criterion entirely in the rubric rendering.  
**Gate:** unit test: lead with `headcount_range = NULL` + all other rubric criteria passing → stage `qualification`, not `rejected`.

### Phase 8 — API and UI query updates
- Add `/api/v1/links/{link_id}/leads` endpoint (reads `link_leads`).
- Update `/api/v1/customers/{customer_id}` response to include `source_links` (via `link_leads → links`).
- Update `/api/v1/contacts` to accept queries by `customer_id`.  
**Gate:** integration test: create two leads from one link → GET link shows both leads; GET customer shows contributing links.

### Phase 9 — Non-blocking agent execution (threading)
- Replace `BackgroundTasks` in `POST /campaigns/{id}/trigger` with a dedicated `ThreadPoolExecutor` (4 workers by default, configurable via `ZER0_RUNNER_MAX_WORKERS`). Uvicorn worker threads are never blocked by agent runs.
- Add `campaign_runs` table: `run_id`, `campaign_id`, `tenant_id`, `status` (`pending`/`running`/`completed`/`failed`), `current_node`, `started_at`, `finished_at`, `error`.
- `runner_service.py` owns the executor, writes `campaign_runs` rows on start/finish, and updates `current_node` as each graph node completes.
- 409 CONFLICT if a run is already `running` for the campaign.
- Add `GET /campaigns/{id}/runs` (list all runs for a campaign) and `GET /campaigns/{id}/runs/{run_id}` (single run status + current_node).  
**Gate:** trigger a campaign; immediately call GET /health — must return 200; run completes in background; GET runs/{run_id} shows status transitions.

### Phase 10 — Campaign stats endpoint
- Add `GET /campaigns/{id}/stats` — reads live counts from DB: `total_links`, `total_leads`, `by_stage` (counts per `lead_stage` value), `messages_sent`, `replies_received`.
- Response is computed fresh from the DB on every call (no caching in v1).  
**Gate:** trigger a run; poll `GET /campaigns/{id}/stats` — counts increment as agent progresses through stages.

---

## 5. Out of scope

- Contact dedup across tenants (each tenant is isolated).
- Merging two `customer` rows that were created before this change (data cleanup is a separate task).
- Pagination on `source_links` / `lead_ids` responses (v1: return all).
- LinkedIn as a research source in Phase 4 (web/Tavily only in v1 per existing spec).
- UI changes for the link detail page (UI wiring follows after API is stable).

---

## 6. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Existing `contacts.lead_id` FK used in many query sites | High | Grep for all usages before migration; update in the same PR as the schema change |
| `link_leads` junction creates N+1 queries in the identify node | Medium | Bulk-insert all junction rows after identify node completes; add appropriate index |
| Research web-search increases per-lead latency (3–5 extra HTTP calls) | Medium | Parallelise `scrape_page` calls; add `research_timeout_seconds` config field to `QualificationConfig` |
| Company-size change silently causes previously-rejected leads to pass qualification | Low | Review existing rubric configs for any campaign that uses headcount as a mandatory criterion; emit warning log if criterion is present but ignored |
