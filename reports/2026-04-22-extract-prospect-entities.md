# Implementation Plan: Restructure Pipeline — Links → Leads → Contacts → Outreach

**Date:** 2026-04-22  
**Status:** DRAFT — awaiting review  

---

## Mental Model

```
DISCOVERY         LEADS (stages)                         OUTREACH
──────────        ─────────────────────────────────────  ────────────────────────
Web search   ─┐
LinkedIn     ─┼→  links ──→  lead (prospect)
Directory    ─┘      │           │ research (cumulative)
              │       │           │ qualification (score)
              │       │           │ contacts (org structure)
              │       └───────→   │ approval (human selects contacts)
              │                   │ outreach (per contact)
              │                   └──→ first_contact | no_contact
              │
              └─ one link can surface multiple leads
```

**Link** — A raw URL returned by web search, LinkedIn, or directory. A link is just a pointer to a web page. One link page can reference multiple companies → multiple leads.

**Lead** — A company (or individual) that is a possible customer. The central entity. Has stages:

| Stage | Meaning |
|-------|---------|
| `prospect` | Company identified from a link — name + website known, nothing else yet |
| `research` | Research underway/complete — cumulative knowledge about company growing |
| `qualification` | Scored against ICP rubric — qualified or rejected |
| `contacts` | Contact discovery underway — finding org structure, decision makers |
| `approval` | Awaiting human to approve and select contacts to reach |
| `outreach` | Messaging campaign active — one or more contacts being messaged |
| `first_contact` | Positive reply received from any contact — success |
| `no_contact` | No response after all follow-ups — closed |

**Contact** — Individual person within a lead's company. Extracted during `contacts` stage.

**Outreach** — Approval-gated messaging to selected contacts. Positive reply from any contact stops follow-up to all others for that lead.

---

## Current Problem

- Web search produces links with no company metadata
- The code calls links "raw_leads" — confusion, wrong entity
- Research enriches the link but does NOT extract lead (company) entities
- Qualification receives `lead.company=None` → rejects everything with score 0
- No cumulative research database — each campaign starts from zero
- No contacts stage — outreach goes direct from qualify with no contact list

---

## Goal

Restructure the pipeline to match the mental model: introduce `links` as the discovery output, `leads` as the company entity (identified from links), cumulative research per lead, qualification on actual company data, then contact discovery and approval-gated outreach.

---

## Database Schema Changes

### `spec/product/07-data-model.md`

#### New `links` table — Raw discovery results

One row per URL found during discovery. A single link page can reference (and spawn) multiple leads.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID FK | |
| `campaign_id` | UUID FK | |
| `url` | TEXT | unique per campaign |
| `source` | ENUM: `web`, `linkedin`, `directory` | |
| `page_text` | TEXT | scraped body (may be empty) |
| `scraped_at` | TIMESTAMPTZ | NULL until scraped |
| `created_at` | TIMESTAMPTZ | |

#### Restructured `leads` table — Company entity, not a URL

`leads` becomes the company-level entity. One lead = one company (or individual) that is a possible customer. 

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID FK | |
| `campaign_id` | UUID FK | |
| `link_id` | UUID FK → links.id | source link this lead was identified from |
| `stage` | ENUM (see below) | current pipeline stage |
| `company_name` | TEXT | extracted company name |
| `domain` | TEXT | company website/domain |
| `industry` | TEXT | detected industry |
| `headcount_range` | TEXT | e.g. `"10–50"` |
| `business_type` | ENUM: `enterprise`, `mid_market`, `smb`, `clinic`, `service_provider`, `solo` | |
| `research_summary` | TEXT | cumulative research summary (appended each run) |
| `signals` | JSONB | list of buying signals (appended each run) |
| `score` | NUMERIC | qualification score |
| `per_criterion_scores` | JSONB | |
| `rationale` | TEXT | qualification rationale |
| `rejection_reason` | TEXT | if rejected |
| `last_researched_at` | TIMESTAMPTZ | most recent research run |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Lead stage enum** (replaces old `lead_stage`):
```
prospect → research → qualification → contacts → approval → outreach → first_contact | no_contact
                                                                         └── rejected (at qualification)
```

#### New `contacts` table — Individual people within a lead

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `tenant_id` | UUID FK | |
| `lead_id` | UUID FK → leads.id | |
| `first_name` | TEXT | |
| `last_name` | TEXT | |
| `email` | TEXT | unique per lead |
| `phone` | TEXT | |
| `role` | TEXT | job title |
| `seniority_level` | ENUM: `c_level`, `vp`, `director`, `manager`, `ic`, `other` | |
| `decision_maker_score` | NUMERIC 0–100 | |
| `approved_for_outreach` | BOOLEAN | set during approval stage |
| `outreach_stopped` | BOOLEAN | set when positive reply from another contact |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

#### Update `messages` table — Target specific contact

- Add `contact_id` (UUID FK → contacts.id, nullable)

#### Drop old columns from `leads`

Remove: `name`, `url`, `source`, `enriched_data` (moved to `links` or restructured).

---

### Updated ERD

```
links       ||--o{ leads     : "surfaces"
leads       ||--o{ contacts  : "has"
leads       ||--o{ messages  : "in_campaign"
messages    }o--|| contacts  : "targets"
campaigns   ||--o{ links     : "discovers"
campaigns   ||--o{ leads     : "tracks"
```

---

### `spec/product/10-agent-graph.md` — Updated Graph Flow

```
discover → scrape_links → identify_leads → research → qualify → get_contacts → approval_gate → outreach → check_replies
```

**Nodes:**

| Node | Input | Output | Lead stage transition |
|------|-------|--------|----------------------|
| `discover` | campaign config | `links[]` (URLs) | — |
| `scrape_links` | `links[]` | `links[]` with `page_text` | — |
| `identify_leads` | scraped links | `leads[]` (prospect stage) | → `prospect` |
| `research` | leads in `prospect` or `research` stage | leads with enriched summaries/signals | → `research` |
| `qualify` | research-complete leads | qualified or rejected leads | → `qualification` / `rejected` |
| `get_contacts` | qualified leads | leads with contact lists | → `contacts` |
| `approval_gate` | leads with contacts | human selects contacts per lead | → `approval` |
| `outreach` | approved leads + selected contacts | messages sent | → `outreach` |
| `check_replies` | outreach-active leads | replies processed; positive reply stops others | → `first_contact` / `no_contact` |

**`AgentState` changes:**
- `links: list[Link]` — replaces `raw_leads`
- `leads: list[Lead]` — replaces `enriched_leads` / `qualified_leads` / `rejected_leads` (stage field distinguishes them)
- Remove: `raw_leads`, `enriched_leads`, `qualified_leads`, `rejected_leads`

---

## Engineering Impact

**`spec/engineering/spec-driven.md`** — No new rules required.

**`spec/engineering/secret-hygiene.md`** — Future consideration: prospect emails/contact details require access control on API responses (ensure extracted prospect data is not leaked). Defer to Phase 2.

**Database migrations** — New Alembic migration required; will be auto-generated from SQLAlchemy model changes.

---

## Phases

### Phase 1: Domain Models & Schema (Gate: migration passes)

**Work:**
1. New `Link` Pydantic model (`src/zer0/domain/link.py`) — id, campaign_id, tenant_id, url, source, page_text, scraped_at
2. Replace `RawLead`/`EnrichedLead`/`QualifiedLead`/`RejectedLead` with a single `Lead` model + `LeadStage` enum in `src/zer0/domain/lead.py`; add fields: company_name, domain, industry, headcount_range, business_type, research_summary, signals, score, rejection_reason
3. New `Contact` Pydantic model (`src/zer0/domain/contact.py`) 
4. SQLAlchemy: add `LinkRow`, restructure `LeadRow`, add `ContactRow` (`src/zer0/db/models.py`)
5. Add `contact_id` FK to `MessageRow`
6. Alembic migration: `alembic revision --autogenerate -m "restructure_leads_add_links_contacts"`
7. Verify migration forward/backward

**Test gate:** Schema matches spec; migration clean.

---

### Phase 2: Scrape + Identify Leads Nodes (Gate: nodes return correct types)

**Work:**
1. Rename `node_discover` output: `raw_leads` → `links`
2. Create `node_scrape_links` — scrapes each link's URL, populates `link.page_text`; errors are non-fatal (empty page_text)
3. Create `node_identify_leads` — LLM call per scraped link to extract company entities:
   - Input: `link.page_text`, `link.url` 
   - Output: 1..N `Lead` objects at stage `prospect` (one page can name multiple companies)
   - Dedup by (tenant_id, domain): if lead exists, skip insert; if new, create row
4. New prompt: `src/zer0/prompts/identifier.md` — extract company name, domain, industry, business type from page text; return JSON array

**Test gate:** Single scraped link → 1+ leads with stage=prospect, company_name/domain populated.

---

### Phase 3: Research Node (Cumulative) (Gate: research appends to existing leads)

**Work:**
1. Replace existing `node_research` with cumulative version:
   - Input: leads in `prospect` or `research` stage
   - For each lead: LLM call using company_name, domain, existing research_summary, new signals from scraped data
   - Append new signals to `lead.signals` (JSON array, not overwrite)
   - Update `lead.research_summary` (summarize existing + new)
   - Update `lead.last_researched_at` → stage `research`
2. Update `researcher.md` prompt — accept existing_summary + new page data; produce incremental additions only
3. Unit test: research run twice on same lead; signals accumulate; summary grows

**Test gate:** Second research run on same lead appends signals, does not overwrite.

---

### Phase 4: Qualify Node Update (Gate: no more company=None rejections)

**Work:**
1. Update `qualify_lead` tool — use `lead.company_name`, `lead.research_summary`, `lead.signals` (all real data now instead of None)
2. Update `qualifier.md` prompt — accept structured lead fields
3. Test: mock lead with populated company_name + research_summary → score > 0

**Test gate:** Leads with real company data score > 0; no rejections on "no data" grounds.

---

### Phase 5: Get Contacts Node (Gate: contacts table populated)

**Work:**
1. Create `src/zer0/tools/find_all_contacts.py` stub — input: lead domain + target roles; output: list of Contact objects (empty for now; ready for Hunter.io / Apollo integration)
2. Create `node_get_contacts` — for each qualified lead, call stub, upsert contacts table (dedup by email per lead), emit contact_discovered events, stage → `contacts`
3. Update `node_approval_gate` — show contacts per lead in approval payload; human selects contact_ids; emit approval event with selected_contact_ids

**Test gate:** Qualified lead → contacts stage; approval gate carries contact list.

---

### Phase 6: Outreach + Positive Reply Stopping (Gate: stop logic verified)

**Work:**
1. Update `node_outreach` — create one message per selected contact_id; `messages.contact_id` set
2. Update `check_replies` — if positive reply on any contact for a lead: query all pending messages for that lead, set `contact.outreach_stopped=true`, stop follow-up, emit `outreach.stopped_others` event
3. Integration test: 3 contacts for 1 lead; contact B replies positively → contacts A and C stopped

**Test gate:** Positive reply stops others; first_contact stage reached; event logged.

---

## Out of Scope (Deferred)

- Contact enrichment from external APIs (Hunter.io, Apollo, LinkedIn) — Phase 5 stub only
- Fuzzy dedup for leads identified with slightly different names
- Contact email verification / bounce testing
- Prospect deduplication across campaigns (same company in two campaigns)
- UI for manually merging/editing leads or contacts
- ML-based decision maker scoring

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM identifies wrong company from link page | Bad lead inserted | Confidence score threshold; log extraction payload |
| One link references 10+ companies | Too many leads per campaign | Cap at N leads per link (configurable); log truncation |
| Contact stub returns empty forever | Approval shows no contacts | Fallback: allow approval with no contacts selected (outreach to lead-level email if available) |
| Positive reply detection fails | Spam to other contacts | Unit test; log all stop_on_positive events |
| Schema restructure breaks existing data | Production data lost | Migration adds new columns nullable; old rows not deleted; ran on test DB + reviewed before prod |

---

## Success Criteria

1. ✅ Migration applies cleanly; `links`, `contacts` tables exist; `leads` has new columns
2. ✅ `node_identify_leads` returns at least 1 lead per scraped link (with company_name populated)
3. ✅ Research runs twice on same lead; signals append, not overwrite
4. ✅ Qualification receives non-null company data → scores > 0 on real leads
5. ✅ Contacts table populated after `get_contacts` node
6. ✅ Approval event contains contact_ids
7. ✅ Positive reply stops all other contacts for same lead
8. ✅ Dashboard shows lead stage progression including contacts and outreach

---

## Timeline

| Phase | Work | Days |
|-------|------|------|
| 1 | Domain models + schema + migration | 1 |
| 2 | scrape_links + identify_leads nodes + identifier prompt | 1.5 |
| 3 | Research node (cumulative) | 1 |
| 4 | Qualify update | 0.5 |
| 5 | Get contacts + approval update | 1.5 |
| 6 | Outreach + reply stopping | 1 |
| — | Integration testing | 1 |
| **Total** | | **~7.5 days** |
