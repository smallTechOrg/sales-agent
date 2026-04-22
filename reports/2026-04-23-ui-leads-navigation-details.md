# Project: Elevate Leads to First-Class UI Navigation & Enhance Pipeline Details

**Status:** DRAFT — Awaiting approval before implementation.

**Date:** 2026-04-23

---

## Goal

Make leads a first-class citizen in the dashboard UI by:
1. Adding a **Leads** navigation item in the sidebar (alongside Tenants, Campaigns).
2. Enriching the lead pipeline list table with **source badges** and additional key fields.
3. Expanding the lead detail drawer with **more granular data** (research timeline, signal list, rejection rationale, language detection, per-criterion scoring breakdown).
4. Refactoring the run progress indicator to display only stages **up to qualification** (prospect → research → qualification), since qualified leads move to approval/outreach (operator-driven), not to agent-driven stages.

---

## Spec Impact

### `spec/product/11-ui-dashboard.md` → Additions

All additions are cumulative (no deletions or breaking changes to existing sections).

#### 1. Screen map — add Leads view row

Insert after the "Tenant detail / pipeline view" row:

```
| Leads view (global) | `GET /api/v1/leads?all_campaigns` (tenant scope) |
```

#### 2. Screens in detail — add new "Leads view (global)" section

Insert after "Lead pipeline view" section (or as a parallel section):

```markdown
### Leads view (global)

Global cross-campaign leads table. Can be accessed from the sidebar at any time.

- **Filter bar:** campaign (dropdown), stage, date range, source badge (LinkedIn / web / directory), score range.
- **Lead row:** company name, domain, **source badge**, stage badge, score (if qualified), **last activity**, **research status** (icon: "fresh" / "stale").
- **Lead row details:** on hover or via expandable row, show: contact count, message count, industry, headcount_range, detected_language code.
- **Trigger agent run button:** per-campaign only — dispatches `POST /api/v1/campaigns/{id}/run`.

Clicking a lead row opens the lead detail drawer (same as pipeline view).

**Note:** This view is read-only. Operators still perform approval and message editing in the approval queue and campaign pipeline contexts.
```

#### 3. Lead detail section — expand with new fields

Replace the existing "Lead detail" section with enhanced version:

```markdown
### Lead detail

Shows the full enrichment data, qualification scores, and message history for a single lead.

**Sections:**

- **Profile:** `company_name`, `domain`, `industry`, `headcount_range`, `detected_language` (ISO 639-1 code with flag emoji), stage badge, score, **source badge** (web/linkedin/directory from `links.source`).

- **Research timeline:** 
  - `last_researched_at` formatted as relative time ("2 days ago").
  - Summary of research runs (count, earliest and latest timestamps).
  - Icon badge: 🟢 Fresh (< 7 days) / 🟡 Stale (7–30 days) / 🔴 Needs refresh (> 30 days).

- **Research data:** `research_summary` (cumulative text), `signals` (bulleted list of buying-intent signals with timestamp each signal was detected).

- **Qualification scores:** 
  - **Only shown when stage ≥ `qualification`.**
  - Per-criterion table: criterion name, weight, score, benchmark (optional).
  - Total score + threshold + pass/fail badge.
  - LLM rationale text.
  - **New:** If stage = `rejected`, show rejection reason in a dismissible alert with red background.

- **Rejection info (if rejected):**
  - `rejection_reason` (text, why the lead was rejected).
  - Timestamp when rejected.
  - Option to "unblock" or "retarget" (future) to operator.

- **Contacts:** list of `Contact` rows for this lead. Each contact shows name, role, email, seniority level, `decision_maker_score`, approval status, and `outreach_stopped` flag. Operator can set `approved_for_outreach` per contact from this view. **Only shown when stage ≥ `contacts`.**

- **Messages:** chronological list of sent/pending messages with channel badge, status, and body preview. Expandable to full body. Each row shows the contact the message targeted.

- **Replies:** inbound replies with associated contact and sentiment badge (`positive` / `neutral` / `negative`).

- **Events:** filtered event log for this lead, showing all state transitions and agent actions chronologically.
```

#### 4. Lead pipeline view section — update with source badge

Replace the existing "Lead pipeline view" section with:

```markdown
### Lead pipeline (per campaign)

The core operational screen per campaign. Shows all leads in their current stage with filtering and sorting.

Pipeline stages flowchart — **unchanged**:

```
prospect → research → qualification
                        ├→ contacts → approval → outreach
                        │                        ├→ first_contact
                        │                        ├→ no_contact
                        │                        └→ blocked
                        └→ rejected
```

- **Filter bar:** stage, date range, source (LinkedIn / web / directory), score range.
- **Lead row:** company name, domain, **source badge** (web/linkedin/directory), stage badge, score (if qualified), last activity timestamp, **research freshness icon**.
- **Trigger agent run button:** dispatches `POST /api/v1/campaigns/{id}/run` and shows a **gated progress indicator** reading from `GET /api/v1/events?campaign_id=...`.

Clicking a lead row opens the lead detail drawer.
```

#### 5. Run progress indicator — replace section

Find the existing trigger button description in "Lead pipeline view" and add a new subsection:

```markdown
#### Run progress indicator (gated view)

When `POST /api/v1/campaigns/{id}/run` is triggered, the UI shows a live progress bar that:

- Displays **only the stages up to and including `qualification`:**
  1. Discover
  2. Scrape
  3. Identify
  4. Research
  5. Qualify

- **Purpose:** Rejection happens at the qualification gate; rejected leads require no further action from the agent. Qualified leads then require operator approval, which is not an agent stage. The progress bar is therefore scoped to the agent's decision-making phases only.

- **UI pattern:** Horizontal flow chart with 5 circles/boxes, each circle lights up as the stage completes. Current stage is highlighted in progress color. Completed stages are green. Future stages are gray. Errors abort and show red.

- **Data source:** Real-time polling of `GET /api/v1/events?campaign_id=...&since=<timestamp>` every 2 seconds while a run is `status=running`.

- **Refresh:** `events.event_type` values matched: `link.discovered`, `link.scraped`, `lead.identified`, `lead.researched`, `lead.qualified` (or `lead.rejected`, which completes the flow at the qualification gate).
```

---

## Engineering Impact

- **No schema changes.** All required data is already in `leads` (link_id to fetch source via join), `events` (for progress), and `links` table.
- **API changes (Frontend contract):** No NEW endpoints needed. Existing endpoints (`/api/v1/leads`, `/api/v1/events`) already return the necessary data. *However*, the frontend will need to filter and interpret additional fields:
  - `lead.link_id` → join to `links.source` to get source badge.
  - `lead.detected_language` is already returned.
  - `lead.rejection_reason` is already returned.
  - `events.event_type` for progress states.
- **Frontend implementation scope:** React components and UI logic only. No backend code changes required (assuming API already returns these fields — verify in Phase 1).

---

## Phases

### Phase 1: Audit & Validation

**Gate test:** Confirm all required fields are returned by `/api/v1/leads/{id}` and `/api/v1/leads?campaign_id=...` endpoints.

**Deliverables:**
- Verify that `leads` row includes: `link_id`, `rejected_reason`, `detected_language`, `per_criterion_scores`, `rationale`, `last_researched_at`.
- Verify that joining `lead.link_id → links.source` returns the source enum (`web`, `linkedin`, `directory`).
- Verify that `events.event_type` for the run progress includes the 5 stage names: `link.discovered`, `link.scraped`, `lead.identified`, `lead.researched`, `lead.qualified` (or `lead.rejected`).
- If any field is missing, the backend API must be enhanced to return it before proceeding to Phase 2.
- Document findings in this plan's "Verification steps" section.

---

### Phase 2: Sidebar Navigation Changes

**Goal:** Add a top-level **Leads** navigation item alongside Tenants and Campaigns.

**Context:**
- Current sidebar: Dashboard → Tenant list → Tenant detail (with campaign tabs).
- New: Dashboard → Tenants / Campaigns / **Leads** (three top-level tabs at dashboard or per-tenant scope — **to be clarified**).

**Question for user:** Should the Leads view be:
- **Option A:** Global (all campaigns, all tenants) — single top-level tab.
- **Option B:** Per-tenant (all campaigns within a tenant) — a tab within tenant detail.
- **Option C:** Both — global tab + per-tenant tab under tenant detail.

**Deliverables (assuming Option B per-tenant for now):**
- Add a **Leads** tab in the tenant detail view, alongside any existing tabs (e.g., Campaigns, Settings, etc.).
- Leads tab loads and displays the "Leads view (global, per tenant)" as described in spec.
- Navigation links work (clicking a lead row opens detail drawer).
- Verify no navigation regressions in the existing Campaigns pipeline view.

**Gate test:** Manual smoke test:
1. Log in → navigate to a tenant.
2. Click Leads tab.
3. See the leads table load with source badges, filters work, lead row is clickable, detail drawer opens.
4. Existing Campaigns tab still works identically.

---

### Phase 3: Lead Table Enhancements

**Goal:** Enrich the lead table display with source badge, research freshness icon, and hover details.

**Columns to add / enhance:**

| Column | Current | New |
|---|---|---|
| Company | ✓ | ✓ (no change) |
| Domain | ✓ | ✓ (no change) |
| **Source** | ✗ | 🆕 Badge: 🌐 web / 💼 linkedin / 📚 directory |
| **Freshness** | ✗ | 🆕 Icon: 🟢 < 7 days / 🟡 7–30 / 🔴 > 30 days |
| Stage | ✓ | ✓ (no change) |
| Score | ✓ | ✓ (only if qualified; otherwise blank) |
| **Last activity** | ✓ (timestamp) | ✓ Enhance: relative time ("2 days ago") |
| **Hover detail** | ✗ | 🆕 On hover, show: contacts count, message count, industry, headcount_range, language code |

**Deliverables:**
- Source badge renders correctly using data from `lead.link_id → links.source`.
- Freshness icon calculates from `lead.last_researched_at` using current time.
- Hover state shows additional fields in a tooltip or mini-card.
- Sorting and filtering works with new columns (optional for v1 if not already supported).

**Gate test:**
1. Load leads table with multiple leads from different sources.
2. Verify source badges are correct (spot-check 3 leads against known sources).
3. Verify freshness icons appear and update correctly.
4. Hover over a lead row; verify tooltip shows contacts, messages, industry, language.

---

### Phase 4: Lead Detail Page Enhancements

**Goal:** Expand the lead detail drawer with timeline, signals list, rejection reason, and scoring breakdown.

**Sections to add / enhance:**

| Section | Current | Enhancement |
|---|---|---|
| **Profile** | Name, domain, industry, headcount, stage, score | 🆕 Add: source badge, detected_language (with emoji) |
| **Research timeline** | ✗ | 🆕 Add: `last_researched_at`, freshness icon with color, "Researched N times" badge, with timestamp range |
| **Research data** | `research_summary` + `signals` list | Enhance: Show signal list with bullet points, optionally with timestamps if available in payload |
| **Qualification** | Per-criterion table + score + rationale | Enhance: Add weight column, benchmark column (if available), better formatting |
| **Rejection info** | ✗ | 🆕 Only if stage=rejected: Show `rejection_reason` in red alert box with timestamp |
| **Contacts** (stage ≥ contacts) | ✓ | ✓ (no change) |
| **Messages** | ✓ | ✓ (no change) |
| **Replies** | ✓ | ✓ (no change) |
| **Events** | ✓ | ✓ (no change) |

**Rendering rules:**
- Profile section always visible.
- Research timeline: always visible.
- Research data: always visible (prior to qualify stage, may be empty).
- Qualification scores: shown **only if stage ≥ `qualification`**.
- Rejection info: shown **only if stage = `rejected`**.
- Contacts section: shown **only if stage ≥ `contacts`**.
- Messages/Replies/Events: always visible.

**Deliverables:**
- Expand lead detail component to render all new sections.
- Conditionally hide/show sections based on stage.
- Format timestamps as relative time and absolute time (on hover).
- Style rejection alert with red background and clear dismiss button.

**Gate test:**
1. Open lead detail for a lead at stage = `prospect` (research). Verify only Profile, Research timeline, Research data visible. Others hidden.
2. Open lead detail for a lead at stage = `qualification` (qualified). Verify Qualification scores section visible with per-criterion breakdown.
3. Open lead detail for a lead at stage = `rejected`. Verify red rejection alert appears with reason and timestamp.
4. Verify all timestamps are relative time (e.g., "2 days ago") with absolute time on hover.

---

### Phase 5: Run Progress Indicator Refactor

**Goal:** Update the progress indicator to show **only stages up to `qualification`**, not all stages.

**Current behavior (inferred from spec):**
- Horizontal progress bar showing all lead stages: prospect → research → qualification → contacts → approval → outreach → [terminal stages].
- Progress updates via real-time polling of `events?campaign_id=...`.

**New behavior:**
- Horizontal progress bar showing **only 5 stages**:
  1. Discover
  2. Scrape
  3. Identify
  4. Research
  5. Qualify

- **State mapping** (from `events.event_type`):
  - `link.discovered` → Discover (🟢 complete)
  - `link.scraped` → Scrape (🟢 complete)
  - `lead.identified` → Identify (🟢 complete)
  - `lead.researched` → Research (🟢 complete)
  - `lead.qualified` → Qualify (🟢 complete) **OR** `lead.rejected` → Qualify (⚠️ some rejected, some qualified)

- **Current stage highlighting:** The stage currently executing is highlighted in a different color (e.g., yellow/gold).
- **Error state:** If an event shows an error (e.g., node failed), display red × and show error message.
- **Completion:** When the final `lead.qualified` or any `lead.rejected` event appears, mark Qualify as complete and hide the progress bar after 2 seconds.

**Deliverables:**
- Refactor progress indicator component to display 5-stage flow only.
- Update event polling handler to map `events.event_type` to stage indices.
- Update stage color logic: gray (future) → yellow (current) → green (complete) → red (error).
- Test with a live campaign run.

**Gate test:**
1. Manually trigger a campaign run via the dashboard.
2. Observe progress indicator: 5 stages displayed in order.
3. Verify each stage transitions correctly as events arrive.
4. Verify bar completes when final stage reaches completion.
5. Stop progress indicator and verify it auto-hides after 2 seconds.
6. (Bonus) Manually inject a failed event; verify error state displays.

---

### Phase 6: Visual Polish & Cross-browser Testing

**Goal:** Ensure all new UI elements are polished and tested across browsers.

**Deliverables:**
- Responsive design: Test lead table and detail drawer on mobile, tablet, desktop.
- Dark mode (if applicable): Verify all new colors are readable in dark/light themes.
- Accessibility: Verify all badges and icons have alt text or title attributes.
- Loading states: Add spinners / skeletons while data loads.
- Error states: Verify error boundaries catch and display gracefully.

**Gate test:**
- Manual QA checklist on desktop (Chrome, Safari) and mobile (iOS Safari, Android Chrome).
- Run accessibility checker (axe or similar).
- Test with network throttling (slow 3G).

---

## Out of Scope

1. **Leads-only mode:** Operators can still only view leads within the context of campaigns; there is no "leads without a campaign" concept in v1.
2. **Lead bulk actions:** Bulk edit, bulk approve, bulk reject — deferred to v2.
3. **Advanced lead search/filters:** Beyond stage, date range, source, and score range. Keyword search on company name is also out of scope for the underlying API (would be a separate backend feature).
4. **Lead ranking/sorting by custom criteria:** Default sort is by last activity; custom column sorts are out of scope.
5. **Export leads to CSV/Excel:** Out of scope.
6. **Leads API pagination enhancements:** Assume existing pagination works; no new pagination logic.
7. **Webhook subscriptions for lead events:** Out of scope.
8. **Integration with external lead databases:** Out of scope.

---

## Risks

| Risk | Mitigation |
|---|---|
| API doesn't return all required fields | **Phase 1 validation catches this.** If missing, backend PR required before frontend dev. |
| Performance: loading large lead lists (1000s of leads) | Use pagination (existing), add debouncing to filters, lazy-load hover details. |
| Source badge incorrectly mapped (link_id missing or joined incorrectly) | Comprehensive test in Phase 3 with known links from all sources. |
| Rejected leads still show in "qualification stage" UI | Conditional rendering by stage field, tested in Phase 4's rejected lead test. |
| Events polling stale/delayed | Implement exponential backoff on polling; if delay > 10 seconds, show warning banner. |
| Progress indicator stays visible after run completes (janky UX) | Auto-hide after 2 seconds (Phase 5); test with actual run. |

---

## Verification Steps

**Pre-implementation (Phase 1):**
- [ ] Query `/api/v1/leads/{id}` for a lead at each stage (prospect, qualified, rejected); verify response includes `link_id`, `detected_language`, `rejection_reason`, `per_criterion_scores`, `rationale`, `last_researched_at`.
- [ ] Query `/api/v1/links/{id}` and verify `source` enum is present and correct.
- [ ] Query `/api/v1/events?campaign_id=<id>` from a recent run; verify `event_type` includes all 5: `link.discovered`, `link.scraped`, `lead.identified`, `lead.researched`, `lead.qualified` (and `lead.rejected` if rejected leads exist).
- [ ] Document any missing fields and raise a backend task.

**Post-implementation (End-to-end test):**
- [ ] Run a full campaign from start to finish (discovery → qualification).
- [ ] Verify progress indicator shows all 5 stages and completes correctly.
- [ ] Open a qualified lead detail; verify all sections render (Profile, Research, Qualification, Contacts).
- [ ] Open a rejected lead detail; verify rejection alert shows.
- [ ] Navigate to Leads tab; verify source badges render correctly for 3+ leads.
- [ ] Filter leads by source; verify filter works.
- [ ] Test on mobile; verify responsive layout works.

---

## References

- **Spec:** [`spec/product/11-ui-dashboard.md`](../../spec/product/11-ui-dashboard.md)
- **Data model:** [`spec/product/07-data-model.md`](../../spec/product/07-data-model.md) (Lead, Link, Events tables)
- **Contact table operations:** `spec/product/04-capabilities/07-contact-discovery.md` (if exists)

