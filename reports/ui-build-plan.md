# UI Dashboard Build Plan

**Date:** 2026-04-21  
**Slug:** ui-build-plan  
**Status:** DRAFT — awaiting approval before implementation begins.

---

## 1. Goal

Build the Next.js 15 operator dashboard at `ui/` in the repo root, per
`spec/product/11-ui-dashboard.md`. The dashboard communicates exclusively with the
existing FastAPI backend over REST; backend auth is currently header-only
(`X-Tenant-ID`), so no login page is required. Every phase ships as a
self-contained, independently reviewable PR.

---

## 2. Spec Impact

All changes are additive — no existing `spec/product/` file needs edits.  
The following spec/implementation **gaps** were found during the audit and must be
tracked; the UI plan notes workarounds so frontend work is not blocked:

| Gap | Spec reference | Current API | Workaround in UI |
|-----|---------------|-------------|-----------------|
| List all tenants | spec §Screen map: `GET /api/v1/tenants` | **Does not exist.** Only `GET /api/v1/tenant` (single, scoped to `X-Tenant-ID`) | UI maintains a `localStorage` list of known tenant IDs; calls `GET /api/v1/tenant` per entry |
| Create tenant | spec §Onboarding wizard: `POST /api/v1/tenants` | **Does not exist.** | Onboarding wizard is built but the "Create" step UI renders with a "not yet implemented" guard until the backend endpoint ships |
| Events `since` filter | spec §Observability: `GET /api/v1/events?…&since=` | `events.py` has no `since` param (only `from`/`to` unimplemented) | Poll with `?from=<last-seen-ts>` — matching the closest existing param name until full filter lands |

---

## 3. Engineering Impact

No rule in `spec/engineering/` is changed. The following rules **apply to the UI
code**:

- `secret-hygiene.md`: secret inputs are `type=password`, never pre-filled, never
  stored in `localStorage`/`sessionStorage`. The API never returns secret values.
- `tenant-isolation.md`: every fetch must carry `X-Tenant-ID: <activeTenantId>`.
  The API client (Phase 1) enforces this at the call-site so individual pages
  cannot forget it.
- `spec-driven.md`: UI changes that require new API endpoints must be spec'd in
  `spec/product/09-api.md` before the backend work starts.

---

## 4. Package Dependencies

Install once during Phase 0. These are the **exact** production + dev dependencies.

```json
// package.json (top-level keys only)
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@types/node": "^22.0.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/postcss": "^4.0.0",
    "postcss": "^8.0.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "^15.0.0"
  }
}
```

No data-fetching library is committed to — the spec does not name one. Phases use
the native `fetch` API wrapped in typed helper functions in `lib/api.ts`.

---

## 5. Shared Layout / Architecture Decisions

### 5.1 Tenant Context

`lib/tenant-context.tsx` exports a React `Context` and `<TenantProvider>` that
stores `activeTenantId: string | null` and a `setActiveTenantId` setter. The
provider reads/saves the value from `localStorage` under key `zer0:activeTenant`.

Every page component reads `activeTenantId` from the context; the API client
(below) reads it automatically. No page needs to pass it manually.

### 5.2 API Client (`lib/api.ts`)

Single module. Reads `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) and
`activeTenantId` from context. Exports typed async functions for every endpoint.
Every request automatically attaches:

```
Content-Type: application/json
X-Tenant-ID: <activeTenantId>
```

The client throws a typed `ApiError` on non-2xx responses so error boundaries can
render the error banner.

### 5.3 App Router Layout

```
app/
  layout.tsx          ← RootLayout: wraps everything in TenantProvider + RootShell
  globals.css         ← @import "tailwindcss"
  page.tsx            ← Dashboard home (tenant list)
  tenants/
    new/page.tsx      ← Onboarding wizard
  [tenantId]/
    layout.tsx        ← Sets activeTenantId from route params; renders per-tenant nav
    page.tsx          ← Tenant detail (campaign list)
    campaigns/
      new/page.tsx
      [campaignId]/
        page.tsx      ← Lead pipeline
        edit/page.tsx
    leads/
      [leadId]/page.tsx
    approvals/page.tsx
    messages/page.tsx
    events/page.tsx
    offerings/
      new/page.tsx
      [offeringId]/edit/page.tsx
    settings/page.tsx
```

### 5.4 Sidebar Navigation

`components/layout/Sidebar.tsx` — fixed left sidebar, 64 px wide.  
Links:

| Label | Route |
|-------|-------|
| Home (all tenants) | `/` |
| ← (active tenant name) | `/<tenantId>` |
| Campaigns | `/<tenantId>` (with campaign tab active) |
| Approvals | `/<tenantId>/approvals` |
| Messages | `/<tenantId>/messages` |
| Events | `/<tenantId>/events` |
| Settings | `/<tenantId>/settings` |

The sidebar collapses the tenant-scoped links when no tenant is active.

### 5.5 Top Bar

`components/layout/TopBar.tsx` — shows the app name "Zer0" and the active
tenant's name (or "No tenant selected"). Includes a tenant-selector dropdown that
lists all known tenants (from `localStorage`).

### 5.6 Tenant Context Header

`components/layout/TenantHeader.tsx` — rendered at the top of every
`[tenantId]/layout.tsx`. Shows: tenant name, tenant ID (truncated UUID), status
badge, and a "New Campaign" quick-action button.

---

## 6. Phases

Each phase gate is a verifiable condition. All phases are **additive** — no phase
removes or breaks earlier work.

---

### Phase 0 — Project Scaffold

**Goal:** A compilable, deployable Next.js 15 shell with no data yet.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/package.json` | Dependencies (see §4) + scripts: `dev`, `build`, `lint` |
| `ui/tsconfig.json` | TypeScript config, strict mode, path alias `@/*` → `./src/*` |
| `ui/next.config.ts` | Static export (`output: 'export'`), `trailingSlash: true` |
| `ui/postcss.config.mjs` | `@tailwindcss/postcss` plugin |
| `ui/tailwind.config.ts` | Tailwind v4 config, content glob `./src/**/*.{ts,tsx}` |
| `ui/.env.local.example` | `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| `ui/.gitignore` | `.next/`, `out/`, `node_modules/` |
| `ui/src/app/globals.css` | `@import "tailwindcss"` |
| `ui/src/app/layout.tsx` | RootLayout skeleton (html, body, `{children}`) |
| `ui/src/app/page.tsx` | Placeholder "Dashboard — coming soon" |

**Gate:** `cd ui && npm install && npm run build` exits 0. TypeScript strict check
passes. `out/` directory exists.

---

### Phase 1 — Tenant Context, API Client, Layout Shell

**Goal:** Wire the tenant context + typed API client + full shared layout. No real
pages yet — layout is visible with mocked tenant name.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/lib/api.ts` | Typed API client (all endpoints, fetch-based) |
| `ui/src/lib/tenant-context.tsx` | `TenantContext`, `TenantProvider`, `useTenant` hook |
| `ui/src/lib/constants.ts` | `API_BASE`, known tenant cache key |
| `ui/src/components/layout/Sidebar.tsx` | Fixed sidebar with nav links |
| `ui/src/components/layout/TopBar.tsx` | Top bar with tenant selector dropdown |
| `ui/src/components/layout/TenantHeader.tsx` | Per-tenant context strip |
| `ui/src/components/ui/ErrorBanner.tsx` | Dismissible red error banner |
| `ui/src/components/ui/Spinner.tsx` | Loading spinner |
| `ui/src/components/ui/Badge.tsx` | Status badge (ok/degraded/disabled) |
| `ui/src/app/layout.tsx` | Updated: wraps in `TenantProvider` + `Sidebar` + `TopBar` |
| `ui/src/app/[tenantId]/layout.tsx` | Sets active tenant from route, renders `TenantHeader` |

**API calls in this phase:** `GET /api/v1/health` (called by `api.ts` health-check
function; used later to show status in the top bar).

```
Method:  GET
Path:    /api/v1/health
Headers: (none required — no auth)
```

**Gate:** `npm run build` passes. Layout renders in browser at `localhost:3000` with
sidebar and top bar visible when running `npm run dev`.

---

### Phase 2 — Dashboard Home (Tenant List)

**Goal:** Render a list of all known tenants with their name and health status.

**Important constraint:** `GET /api/v1/tenants` does not exist. The UI stores a list
of tenant IDs in `localStorage` (key: `zer0:knownTenants`). For each stored ID it
calls `GET /api/v1/tenant` to fetch name and status. The dashboard page iterates the
localStorage list and renders one row per tenant.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/page.tsx` | Dashboard home page (replaces placeholder) |
| `ui/src/components/tenant/TenantTable.tsx` | Table: ID, Name, Status, Actions |
| `ui/src/components/tenant/TenantCard.tsx` | Single tenant row / card |
| `ui/src/hooks/useTenants.ts` | Hook: reads localStorage list, fetches each tenant |

**API calls:**

```
Method:  GET
Path:    /api/v1/tenant
Headers: Content-Type: application/json
         X-Tenant-ID: <tenantId>   ← called once per known tenant ID
```

```
Method:  GET
Path:    /api/v1/health
Headers: (none)
```

**User actions:**
- "New Tenant" button → navigates to `/tenants/new` (Phase 3).
- Clicking a tenant row → navigates to `/<tenantId>`.
- "Add Existing Tenant" shortcut → prompts for a UUID and adds it to
  `localStorage` list (allows pointing the UI at a tenant that already exists in
  the DB).

**Gate:** Dashboard page renders without runtime errors when localStorage contains
at least one tenant ID. Tenant data fetched from a running backend is displayed
correctly. Empty-state ("No tenants yet") is shown when localStorage list is empty.

---

### Phase 3 — Tenant Onboarding Wizard

**Goal:** Multi-step guided wizard: Identity → Credentials → Offering → Campaign →
Review.

**Important constraint:** `POST /api/v1/tenants` does **not** exist in the current
backend. Phase 3 builds the entire wizard UI; the "Create Tenant" step renders an
"API endpoint not yet implemented — upgrade the backend to unblock" error state
until the backend ships. All subsequent steps (Offering, Campaign) are fully
functional once a tenant ID exists.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/tenants/new/page.tsx` | Wizard shell — manages `step` state |
| `ui/src/components/forms/TenantIdentityForm.tsx` | Step 1: name input |
| `ui/src/components/forms/CredentialsForm.tsx` | Step 2: Gmail, WhatsApp, Slack fields (`type=password`, never pre-filled) |
| `ui/src/components/forms/OfferingForm.tsx` | Step 3: offering fields |
| `ui/src/components/forms/CampaignForm.tsx` | Step 4: full campaign config form |
| `ui/src/components/forms/WizardReview.tsx` | Step 5: summary with edit links, secrets shown as `••••••` |
| `ui/src/components/ui/SecretInput.tsx` | `type=password` input, always empty on mount |
| `ui/src/components/ui/StepIndicator.tsx` | Wizard step breadcrumb |

**API calls (wizard steps):**

Step 1 — Identity (client-side only, no API call).

Step 2 — Tenant creation (**GAP — not yet implemented**):
```
Method:  POST
Path:    /api/v1/tenants       ← DOES NOT EXIST YET
Headers: Content-Type: application/json
         X-Tenant-ID: (not applicable — tenant is being created)
Body:    { "name": "<string>" }
```

Step 3 — Save Offering (after tenant exists):
```
Method:  POST
Path:    /api/v1/offerings
Headers: Content-Type: application/json
         X-Tenant-ID: <new-tenant-id>
Body:    OfferingCreate object
```

Step 4 — Save Campaign:
```
Method:  POST
Path:    /api/v1/campaigns
Headers: Content-Type: application/json
         X-Tenant-ID: <new-tenant-id>
Body:    CampaignCreate object
```

Step 5 — Enable Tenant (PATCH):
```
Method:  PATCH
Path:    /api/v1/tenant
Headers: Content-Type: application/json
         X-Tenant-ID: <new-tenant-id>
Body:    { "enabled": true }    ← Note: current PATCH /tenant does not expose
                                   "enabled". Backend schema addition required.
```

**User actions:**
- "Next" advances the step after client-side validation.
- Edit links return to a specific step.
- "Save & Enable" toggle on the review step.
- On completion: tenant ID added to `localStorage` list; redirects to `/<tenantId>`.

**Gate:** Wizard renders all five steps correctly. Client-side validation (empty name,
required fields) prevents "Next" from advancing. Credentials are `type=password` and
verified never pre-filled on mount.

---

### Phase 4 — Tenant Detail & Campaign List

**Goal:** Per-tenant home page (campaign list) and campaign creation.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/[tenantId]/page.tsx` | Tenant home: campaign list + "New Campaign" button |
| `ui/src/components/campaign/CampaignCard.tsx` | Campaign row: name, status, offering, approval mode |
| `ui/src/components/campaign/CampaignTriggerButton.tsx` | "Run now" button with loading state |
| `ui/src/app/[tenantId]/campaigns/new/page.tsx` | New campaign page (embeds `CampaignForm`) |
| `ui/src/app/[tenantId]/campaigns/[campaignId]/edit/page.tsx` | Edit campaign page |
| `ui/src/hooks/useCampaigns.ts` | Fetch + cache campaigns for active tenant |
| `ui/src/hooks/useOfferings.ts` | Fetch offerings (for the offering select in CampaignForm) |

**API calls:**

```
Method:  GET
Path:    /api/v1/campaigns
Headers: X-Tenant-ID: <activeTenantId>
Query:   cursor, limit
```

```
Method:  GET
Path:    /api/v1/offerings
Headers: X-Tenant-ID: <activeTenantId>
Query:   cursor, limit
```

```
Method:  POST
Path:    /api/v1/campaigns
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    CampaignCreate
```

```
Method:  GET
Path:    /api/v1/campaigns/{id}
Headers: X-Tenant-ID: <activeTenantId>
```

```
Method:  PATCH
Path:    /api/v1/campaigns/{id}
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    CampaignPatch (partial)
```

```
Method:  POST
Path:    /api/v1/campaigns/{id}/trigger
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    {} (empty)
Response 202: { run_id, message }
```

**User actions:**
- Clicking a campaign card → navigates to `/<tenantId>/campaigns/<campaignId>` (Phase 5).
- "Run now" button → calls `POST /campaigns/{id}/trigger`, shows spinner, disables
  button while run is in progress (detects via 409 response on re-click).
- "New Campaign" → `/tenants/<tenantId>/campaigns/new`.
- "Edit" icon → `/tenants/<tenantId>/campaigns/<id>/edit`.
- "Delete" → `DELETE /api/v1/campaigns/{id}`, confirms with inline confirmation.

```
Method:  DELETE
Path:    /api/v1/campaigns/{id}
Headers: X-Tenant-ID: <activeTenantId>
```

**Gate:** Campaign list renders real data from a running backend. "Run now" posts the
trigger successfully and the button disables. TypeScript has no errors.

---

### Phase 5 — Lead Pipeline & Lead Detail

**Goal:** Per-campaign lead pipeline view and lead detail drawer.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/[tenantId]/campaigns/[campaignId]/page.tsx` | Lead pipeline page |
| `ui/src/components/lead/LeadTable.tsx` | Filterable/sortable lead table |
| `ui/src/components/lead/LeadRow.tsx` | Row: company, stage badge, score, last activity |
| `ui/src/components/lead/LeadFilterBar.tsx` | Stage / date / source / score filters |
| `ui/src/app/[tenantId]/leads/[leadId]/page.tsx` | Lead detail page |
| `ui/src/components/lead/LeadProfile.tsx` | Profile section |
| `ui/src/components/lead/QualificationScores.tsx` | Per-criterion score table |
| `ui/src/components/lead/LeadMessagesSection.tsx` | Message list within lead detail |
| `ui/src/components/lead/LeadEventsSection.tsx` | Events filtered to this lead |
| `ui/src/hooks/useLeads.ts` | Fetch + filter leads for a campaign |
| `ui/src/hooks/useEvents.ts` | Fetch events (shared, filterable) |
| `ui/src/hooks/useMessages.ts` | Fetch messages (shared, filterable) |

**API calls:**

```
Method:  GET
Path:    /api/v1/leads
Headers: X-Tenant-ID: <activeTenantId>
Query:   campaign_id=<id>, stage=<stage>, cursor, limit
```

```
Method:  GET
Path:    /api/v1/leads/{id}
Headers: X-Tenant-ID: <activeTenantId>
```

```
Method:  PATCH
Path:    /api/v1/leads/{id}
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    LeadPatch (stage | contact_email | contact_role)
```

```
Method:  POST
Path:    /api/v1/leads/{id}/trigger-followup
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    {} (empty)
```

```
Method:  GET
Path:    /api/v1/messages
Headers: X-Tenant-ID: <activeTenantId>
Query:   lead_id=<id>, cursor, limit
```

```
Method:  GET
Path:    /api/v1/events
Headers: X-Tenant-ID: <activeTenantId>
Query:   lead_id=<id>, cursor, limit
```

**Events auto-refresh (polling):** when a run is in progress (detected by presence of
a recent `campaign.run.started` event with no matching `campaign.run.completed`),
the pipeline page polls `GET /api/v1/events?campaign_id=<id>&from=<last-seen-ts>`
every **10 seconds**. Polling stops when a completion event is seen or the user
navigates away (cleanup in `useEffect` return).

**User actions:**
- Filter bar updates query params; leads list re-fetches.
- Clicking a lead row → navigates to `/<tenantId>/leads/<leadId>`.
- "Block lead" toggle → `PATCH /leads/{id}` with `{ "blocked": true }`.
- "Trigger follow-up" button → `POST /leads/{id}/trigger-followup`.
- Messages in lead detail: expandable body preview.

**Gate:** Lead table renders from backend. Filter by stage works. Lead detail page
loads full profile data. Polling does not leak (verified by navigating away and
checking no ongoing network requests).

---

### Phase 6 — Approval Queue

**Goal:** Global approval queue with approve/reject/edit-and-approve actions.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/[tenantId]/approvals/page.tsx` | Approval queue page |
| `ui/src/components/approval/ApprovalQueueTable.tsx` | Table of pending items |
| `ui/src/components/approval/ApprovalRow.tsx` | Row: lead/message details + action buttons |
| `ui/src/components/approval/ApprovalDecisionModal.tsx` | Approve/reject/edit modal |
| `ui/src/hooks/useApprovals.ts` | Fetch pending approvals, refresh after decision |

**API calls:**

```
Method:  GET
Path:    /api/v1/approvals
Headers: X-Tenant-ID: <activeTenantId>
Query:   campaign_id (optional), type (qualify | message), cursor, limit
```

```
Method:  POST
Path:    /api/v1/approvals/leads/{lead_id}/qualify
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    { "decision": "approve" }
      or { "decision": "reject", "reason": "<string>" }
```

```
Method:  POST
Path:    /api/v1/approvals/messages/{message_id}
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    { "decision": "approve", "body": "<optional edited body>" }
      or { "decision": "reject" }
```

**User actions:**
- "Approve" button → opens confirmation modal, submits qualify or message approval.
- "Reject" button → opens rejection modal with optional reason field.
- "Edit & Approve" (messages only) → opens edit modal pre-filled with current body,
  allows editing, submits with `body` field.
- Badge on the sidebar "Approvals" link shows count of pending items (fetched on
  page load and after each decision).
- Empty state: "No pending approvals" — not an error.

**Gate:** Queue renders items. Approve/reject decisions POST to the backend and the
row disappears from the queue on success. Edit & approve pre-fills the message body.

---

### Phase 7 — Messages View & Events Log

**Goal:** Dedicated message browser and event log pages.

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/[tenantId]/messages/page.tsx` | Messages view (filterable by campaign) |
| `ui/src/components/message/MessageTable.tsx` | Table: channel badge, status, subject, sent_at |
| `ui/src/components/message/MessageRow.tsx` | Row with expandable body |
| `ui/src/app/[tenantId]/events/page.tsx` | Events log page |
| `ui/src/components/event/EventLogTable.tsx` | Table: event_type, entity, payload preview, timestamp |
| `ui/src/components/ui/Pagination.tsx` | Shared cursor-based pagination controls |

**API calls (Messages):**

```
Method:  GET
Path:    /api/v1/messages
Headers: X-Tenant-ID: <activeTenantId>
Query:   campaign_id (optional), lead_id (optional), status (optional), cursor, limit
```

```
Method:  GET
Path:    /api/v1/messages/{id}
Headers: X-Tenant-ID: <activeTenantId>
```

**API calls (Events):**

```
Method:  GET
Path:    /api/v1/events
Headers: X-Tenant-ID: <activeTenantId>
Query:   campaign_id (optional), lead_id (optional), event_type (optional),
         from (ISO date), to (ISO date), cursor, limit
```

**User actions:**
- Campaign filter dropdown narrows both messages and events to a single campaign.
- Events table auto-refreshes every 10 seconds while the page is mounted (matches
  spec §Observability).
- Click a message row → expands full body inline.
- Click an event row → expands full `payload` JSON inline.

**Gate:** Both pages render paginated data. Pagination "Load more" works. Auto-refresh
fires at 10-second intervals and stops on unmount.

---

### Phase 8 — Offering Editor

**Goal:** Standalone create/edit offering pages (also usable from within the wizard).

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/[tenantId]/offerings/new/page.tsx` | Create offering |
| `ui/src/app/[tenantId]/offerings/[offeringId]/edit/page.tsx` | Edit offering |
| `ui/src/components/forms/OfferingForm.tsx` | Full offering form (all config sections) |

(Note: `OfferingForm.tsx` was created as a stub in Phase 3 for the wizard; Phase 8
fills in its full implementation including all JSON config subsections.)

**API calls:**

```
Method:  GET
Path:    /api/v1/offerings/{id}
Headers: X-Tenant-ID: <activeTenantId>
```

```
Method:  POST
Path:    /api/v1/offerings
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    OfferingCreate
```

```
Method:  PATCH
Path:    /api/v1/offerings/{id}
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    OfferingPatch (partial)
```

```
Method:  DELETE
Path:    /api/v1/offerings/{id}
Headers: X-Tenant-ID: <activeTenantId>
Response 204: no body
```

**User actions:**
- Full form with all offering fields grouped by section (Identity, ICP, Discovery,
  Qualification, Outreach).
- Rubric criteria: add/remove rows, weight sliders that sum to 1.0 (validated
  client-side before submit).
- Real-time field-level validation.
- Save → redirect back to `/<tenantId>` (campaigns/offerings list).
- Delete → inline confirmation; soft-deletes on the backend.

**Gate:** Create flow posts to backend and redirects. Edit flow pre-fills all fields.
Rubric weight validation prevents submission when weights don't sum to 1.0.

---

### Phase 9 — Tenant Settings Page

**Goal:** Operator-accessible settings for the active tenant (credentials + approval
mode + cooldown).

**Files to create:**

| Path | Purpose |
|------|---------|
| `ui/src/app/[tenantId]/settings/page.tsx` | Settings page |
| `ui/src/components/settings/TenantConfigForm.tsx` | Retargeting cooldown, approval mode |
| `ui/src/components/settings/CredentialsSection.tsx` | Credential fields (presence indicator + write-only inputs) |

**API calls:**

```
Method:  GET
Path:    /api/v1/tenant
Headers: X-Tenant-ID: <activeTenantId>
```

```
Method:  PATCH
Path:    /api/v1/tenant
Headers: Content-Type: application/json
         X-Tenant-ID: <activeTenantId>
Body:    TenantPatch (name | retargeting_cooldown_days | default_approval_mode)
```

**Credential display rules (from `secret-hygiene.md`):**
- Gmail, WhatsApp, Slack fields are `type=password`, **always empty on mount**.
- Presence indicator: the backend returns `google_oauth_configured: true/false`
  (per spec). If `true`, show a green "Configured" badge next to the empty input.
- Submitting an empty credential field **does not** overwrite the stored value (the
  UI omits the field from the PATCH body if it is blank).
- The PATCH body is assembled client-side: only non-empty secret fields are
  included.

**User actions:**
- Edit name, cooldown days, default approval mode → PATCH on save.
- Update credentials: type into a `type=password` input → PATCH includes that
  credential field.
- Save button shows success toast on 200; shows inline error on 4xx.

**Gate:** Settings page loads current tenant config. PATCH with empty credential
fields does **not** send those fields. PATCH with a non-empty credential field sends
the value. TypeScript catches any attempt to read back a secret value from API.

---

## 7. Complete File Index

All paths relative to `ui/`.

### Config / Root

```
package.json
tsconfig.json
next.config.ts
tailwind.config.ts
postcss.config.mjs
.env.local.example
.gitignore
```

### App Shell

```
src/app/globals.css
src/app/layout.tsx
src/app/page.tsx
src/app/tenants/new/page.tsx
src/app/[tenantId]/layout.tsx
src/app/[tenantId]/page.tsx
src/app/[tenantId]/campaigns/new/page.tsx
src/app/[tenantId]/campaigns/[campaignId]/page.tsx
src/app/[tenantId]/campaigns/[campaignId]/edit/page.tsx
src/app/[tenantId]/leads/[leadId]/page.tsx
src/app/[tenantId]/approvals/page.tsx
src/app/[tenantId]/messages/page.tsx
src/app/[tenantId]/events/page.tsx
src/app/[tenantId]/offerings/new/page.tsx
src/app/[tenantId]/offerings/[offeringId]/edit/page.tsx
src/app/[tenantId]/settings/page.tsx
```

### Lib

```
src/lib/api.ts
src/lib/tenant-context.tsx
src/lib/constants.ts
```

### Hooks

```
src/hooks/useTenants.ts
src/hooks/useCampaigns.ts
src/hooks/useLeads.ts
src/hooks/useApprovals.ts
src/hooks/useMessages.ts
src/hooks/useEvents.ts
src/hooks/useOfferings.ts
```

### Layout Components

```
src/components/layout/Sidebar.tsx
src/components/layout/TopBar.tsx
src/components/layout/TenantHeader.tsx
```

### Primitive UI Components

```
src/components/ui/Button.tsx
src/components/ui/Badge.tsx
src/components/ui/Table.tsx
src/components/ui/Input.tsx
src/components/ui/Textarea.tsx
src/components/ui/Select.tsx
src/components/ui/Modal.tsx
src/components/ui/SecretInput.tsx
src/components/ui/ErrorBanner.tsx
src/components/ui/Spinner.tsx
src/components/ui/Pagination.tsx
src/components/ui/StepIndicator.tsx
src/components/ui/Toast.tsx
```

### Feature Components

```
src/components/tenant/TenantTable.tsx
src/components/tenant/TenantCard.tsx
src/components/campaign/CampaignCard.tsx
src/components/campaign/CampaignTriggerButton.tsx
src/components/lead/LeadTable.tsx
src/components/lead/LeadRow.tsx
src/components/lead/LeadFilterBar.tsx
src/components/lead/LeadProfile.tsx
src/components/lead/QualificationScores.tsx
src/components/lead/LeadMessagesSection.tsx
src/components/lead/LeadEventsSection.tsx
src/components/approval/ApprovalQueueTable.tsx
src/components/approval/ApprovalRow.tsx
src/components/approval/ApprovalDecisionModal.tsx
src/components/message/MessageTable.tsx
src/components/message/MessageRow.tsx
src/components/event/EventLogTable.tsx
src/components/forms/TenantIdentityForm.tsx
src/components/forms/CredentialsForm.tsx
src/components/forms/OfferingForm.tsx
src/components/forms/CampaignForm.tsx
src/components/forms/WizardReview.tsx
src/components/settings/TenantConfigForm.tsx
src/components/settings/CredentialsSection.tsx
```

**Total: 16 pages + 35 components + 7 hooks + 3 lib files + 7 config files = 68 files**

---

## 8. Out of Scope

Per spec §Out of scope, and additionally:

- No login page, session cookie, or JWT handling — auth is header-only (`X-Tenant-ID`).
- No lead-facing / tenant-facing portal.
- No live log streaming (polling only).
- No per-operator user accounts.
- No LLM configuration UI (operator settings only covers tenant-level fields; spec
  §Operator settings mentions LLM config but the `GET /PATCH /api/v1/settings`
  operator-level endpoint does not yet exist in the backend — deferred).
- No Fernet key rotation UI (same reason — backend endpoint doesn't exist).
- No `zer0 ui` CLI command integration (Phase 11 — future).
- No test suite in this plan (a separate testing plan should be written).

---

## 9. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| `POST /api/v1/tenants` never ships | Medium | High — wizard cannot complete | Wizard renders gracefully with "not yet implemented" guard; all other pages still work |
| Tailwind CSS v4 breaking changes vs v3 config conventions | Medium | Low — build fails | Read v4 migration docs before Phase 0 |
| Next.js 15 static export limitations (no server actions, no dynamic routes without `generateStaticParams`) | High | Medium — `[tenantId]` routes are dynamic | Add `output: 'export'` + client-side routing only; no server components that fetch; all data fetched client-side in hooks |
| CORS errors when `NEXT_PUBLIC_API_URL` points to a different origin | Medium | High — all API calls fail | Add `allow_origins=["*"]` (dev) or the specific UI origin to FastAPI CORS middleware; note in `.env.local.example` |
| localStorage not available (SSR) | High | Low — hydration mismatch | Guard all `localStorage` reads behind `typeof window !== 'undefined'` |
| `X-Tenant-ID` missing on a page that forgets to set the active tenant | Low | High — 400 error | API client reads from context and throws a typed `MissingTenantError` before the request fires, triggering a redirect to tenant selector |

---

*Plan written per `spec/engineering/workflows/plan.md`. Do not begin implementation
until this plan is approved.*
