# Session Report — feat/cumulative-data — 2026-04-23

**Agent:** GitHub Copilot (GPT-5.4)
**Started:** 2026-04-22T23:24:12Z
**Branch:** feat/cumulative-data
**Goal:** Rename Customers to Companies and Contacts to People, and update the product, API, backend, and UI semantics accordingly.

## Completed steps

### [04:54] Session startup and mandatory spec read
- **What:** Read the mandatory engineering and product spec manifest in full from disk, including lessons and planning workflow rules, then inspected current branch state and existing dirty files.
- **Files:** `spec/product/01-vision.md`, `spec/product/02-architecture.md`, `spec/product/03-tenancy.md`, `spec/product/04-capabilities/01-discovery.md`, `spec/product/04-capabilities/02-enrichment.md`, `spec/product/04-capabilities/03-qualification.md`, `spec/product/04-capabilities/04-outreach.md`, `spec/product/04-capabilities/05-follow-up.md`, `spec/product/04-capabilities/06-reply-handling.md`, `spec/product/04-capabilities/07-contact-discovery.md`, `spec/product/04-capabilities/08-approval.md`, `spec/product/05-config.md`, `spec/product/07-data-model.md`, `spec/product/08-prompts.md`, `spec/product/09-api.md`, `spec/product/10-agent-graph.md`, `spec/product/11-ui-dashboard.md`, `spec/engineering/ai-agents.md`, `spec/engineering/spec-driven.md`, `spec/engineering/secret-hygiene.md`, `spec/engineering/tenant-isolation.md`, `spec/engineering/code-style.md`, `spec/engineering/commits.md`, `spec/engineering/lessons.md`, `spec/engineering/workflows/plan.md`
- **Spec:** `spec/engineering/ai-agents.md`, `spec/engineering/workflows/plan.md`
- **Result:** success

### [04:54] Manifest drift noted
- **What:** Confirmed that the mandatory spec manifest still references `spec/product/06-cli.md`, but that file is currently missing from the repo.
- **Files:** `spec/engineering/ai-agents.md`
- **Spec:** `spec/engineering/ai-agents.md` §2
- **Result:** partial

### [04:54] Rename surface mapped
- **What:** Searched spec, backend, and UI for current `Customer`/`Contact` concepts, `/customers` and `/contacts` routes, and user-facing Customers/Contacts labels. Confirmed the rename affects canonical product nouns, stage labels, API resources, domain models, and UI navigation.
- **Files:** `spec/**`, `src/zer0/**`, `src/ui/src/**`
- **Spec:** `spec/product/01-vision.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`, `spec/product/11-ui-dashboard.md`
- **Result:** success

### [05:45] Backend and graph rename implemented
- **What:** Renamed the domain, ORM, API, graph state, graph node, observability, and people-discovery tool surfaces from Customer/Contact to Company/Person, including stage/state/resource names where these concepts are canonical.
- **Files:** `src/zer0/domain/**`, `src/zer0/db/**`, `src/zer0/api/**`, `src/zer0/graph/**`, `src/zer0/observability/events.py`, `src/zer0/tools/**`
- **Spec:** `spec/product/02-architecture.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`, `spec/product/10-agent-graph.md`
- **Result:** success

### [05:58] UI rename implemented
- **What:** Renamed frontend API client types/methods, hooks, sidebar entries, stage labels, campaign activity labels, and route pages from Customers/Contacts to Companies/People.
- **Files:** `src/ui/src/lib/api.ts`, `src/ui/src/hooks/**`, `src/ui/src/components/layout/Sidebar.tsx`, `src/ui/src/components/lead/LeadTable.tsx`, `src/ui/src/app/[tenantId]/companies/page.tsx`, `src/ui/src/app/[tenantId]/people/page.tsx`, `src/ui/src/app/[tenantId]/campaigns/[campaignId]/page.tsx`, `src/ui/src/app/[tenantId]/leads/page.tsx`
- **Spec:** `spec/product/09-api.md`, `spec/product/11-ui-dashboard.md`
- **Result:** success

### [06:06] Core spec alignment and test updates
- **What:** Updated the main architecture, graph, API, data-model, approval, reply-handling, contact-discovery, and dashboard spec files to make Company/Person canonical, and updated graph unit tests for `get_people` plus person approval IDs.
- **Files:** `spec/product/02-architecture.md`, `spec/product/04-capabilities/06-reply-handling.md`, `spec/product/04-capabilities/07-contact-discovery.md`, `spec/product/04-capabilities/08-approval.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`, `spec/product/10-agent-graph.md`, `spec/product/11-ui-dashboard.md`, `src/tests/unit/graph/test_agent.py`, `src/tests/unit/graph/test_edges.py`
- **Spec:** `spec/product/02-architecture.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`, `spec/product/10-agent-graph.md`, `spec/product/11-ui-dashboard.md`
- **Result:** success

### [06:10] Validation pass
- **What:** Ran workspace diagnostics on the changed UI files, Python tools, and graph unit tests. Updated-source diagnostics passed except for pre-existing unresolved third-party imports in Python files (`httpx`, `structlog`). Attempted Python environment setup, but no environment is currently selected in VS Code, so pytest could not be run.
- **Files:** `src/ui/src/**`, `src/zer0/tools/find_all_people.py`, `src/zer0/observability/events.py`, `src/tests/unit/graph/test_agent.py`, `src/tests/unit/graph/test_edges.py`
- **Spec:** `spec/engineering/code-style.md`
- **Result:** partial

### [06:24] Approval/spec/schema coherence closed
- **What:** Aligned manual approval to person-level selection (`approved_person_ids`), set manual approvals to park leads in `approval`, advanced auto-approved leads to `outreach`, completed the `07-data-model` table rename, added an Alembic schema-rename migration, cleaned remaining canonical product spec wording, and renamed API/tool module files to `companies.py`, `people.py`, and `find_person.py` for code-navigation consistency.
- **Files:** `src/zer0/api/approvals.py`, `src/zer0/graph/nodes.py`, `src/zer0/api/companies.py`, `src/zer0/api/people.py`, `src/zer0/api/__init__.py`, `src/zer0/tools/find_person.py`, `alembic/versions/0007_rename_customers_contacts_to_companies_people.py`, `spec/product/01-vision.md`, `spec/product/02-architecture.md`, `spec/product/04-capabilities/02-enrichment.md`, `spec/product/04-capabilities/03-qualification.md`, `spec/product/04-capabilities/04-outreach.md`, `spec/product/04-capabilities/05-follow-up.md`, `spec/product/04-capabilities/07-contact-discovery.md`, `spec/product/04-capabilities/08-approval.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`
- **Spec:** `spec/product/04-capabilities/08-approval.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`
- **Result:** success

## Pending / next steps

- [ ] Run targeted backend tests once a Python environment is selected in VS Code

## Blockers

- `spec/product/06-cli.md` is referenced by the mandatory manifest but does not exist in the repo.
- The branch already has unrelated modified files; rename work must avoid overwriting those changes.
- No Python environment is selected in VS Code, so runtime validation via pytest is currently blocked.

## Prompt log

| # | User prompt (excerpt ≤ 80 chars) | Agent action summary |
|---|----------------------------------|----------------------|
| 1 | "Rename Customers to Companies. And Rename Contacts to People." | Read mandatory specs, inspected dirty branch state, mapped rename surface, implemented the cross-stack rename, added the schema migration, aligned the approval contract, and validated remaining drift. |