# Plan: CLI Removal & API Drift Fix

**Date:** 2026-04-23  
**Status:** DRAFT (awaiting user approval)

---

## Goal

Remove the CLI subsystem entirely from spec and code to narrow v1 scope to SaaS dashboard + API only. Simultaneously resolve two API endpoint scope ambiguities: implement the missing `POST /leads/{id}/block` endpoint and clarify the intent of `POST /leads/{id}/trigger-followup`.

---

## Spec impact

### Phase 1: Remove CLI from spec

**File:** `spec/product/06-cli.md`
- **Action:** Delete entirely (or gut to a tombstone noting removal). The CLI is operator-facing local tooling incompatible with self-serve SaaS scope.
- **Justification:** v1 scope is dashboard + API for tenants. CLI adds operator-only UX that complicates v1 scope and adds no user value for SaaS.

**File:** `spec/product/01-vision.md`
- **Changes:**
  - Remove any references to CLI from primary user workflows.
  - Update "What Zer0 is" to state: "Tenants configure and operate via a RESTful dashboard API. The agent executes autonomously; no CLI needed."
  - Update success criteria: remove any ref to CLI or operator tasks. Focus on tenant experience only.

---

## Engineering impact

- **`spec/engineering/tenant-isolation.md`:** No change; isolation rules apply to API routes only (not CLI, which is gone).
- **`spec/engineering/code-style.md`:** No change; Python style rules still apply to remaining code.
- **`spec/engineering/secret-hygiene.md`:** No change; secret storage rules still apply to API only.

---

## Phases

### Phase 1: Remove CLI from spec
- **Deliverable:** Gutted `spec/product/06-cli.md` (or deleted if choosing that route); updated `spec/product/01-vision.md` with no CLI references.
- **Test:** Manual review of both files. No broken links in spec/ cross-refs (use link-validator agent).

### Phase 2: Remove CLI implementation
- **Removes:**
  - `src/zer0/cli/` directory (all CLI command handlers).
  - CLI entry points from `src/zer0/__main__.py` (if it exists).
  - `zer0-cli` entry point from `pyproject.toml`.
  - All CLI tests from `src/tests/cli/` (if exists).
  - CLI references from README.md, docs/, and any local test fixtures.
- **Retains:**
  - `src/zer0/settings.py` (needed by API server; do NOT delete).
  - `src/zer0/db/` (needed by API; do NOT delete).
- **Test:** Verify `pytest src/tests/ -v` passes (no CLI test failures since they're gone). Verify app imports cleanly: `python -c "from src.zer0.app import app"`.

### Phase 3: Fix API drift
- **3a. Implement `POST /leads/{id}/block`:**
  - **Current state:** `PATCH /leads/{id}` with `blocked: true` field exists in spec, but endpoint is already handling the blocking logic.
  - **Action:** Clarify in spec: either document that blocking is *only* via `PATCH /leads/{id}` (recommend this), or add explicit `POST /leads/{id}/block` endpoint spec if tooling prefers it.
  - **Recommendation:** Delete the ambiguous `POST /leads/{id}/block` reference from API spec (if it exists separately); confirm `PATCH` is the canonical route.

- **3b. Clarify `POST /leads/{id}/trigger-followup`:**
  - **Current state:** Spec at `spec/product/09-api.md` line ~538 defines endpoint but scope is vague.
  - **Actions:** Either:
    - *Option A (recommend):* Implement per spec — add handler in `src/zer0/api/routes/leads.py` to queue immediate follow-up message.
    - *Option B:* Remove from spec if product decides this is not MVP. Must have written justification.
  - **Decision needed from user:** Keep or remove trigger-followup?

- **Test:** API integration tests for both endpoints pass. `pytest src/tests/integration/api/ -v`.

### Phase 4: Verify
- **Action:** Re-run drift audit via drift-auditor agent. Confirm:
  - No endpoints in spec are unimplemented.
  - No endpoints in code lack spec.
  - No CLI references remain in spec/product/ or src/.
- **Test:** `drift-auditor` returns zero mismatches.

---

## Out of scope

- Dashboard UI implementation (separate effort; not touched here).
- Database schema changes (all data structures stay as-is).
- Tenant onboarding workflows (v1+).
- Authentication/authorization overhaul (stays as-is; JWT inside API).

---

## Risks

| Risk | Mitigation |
|------|-----------|
| `src/zer0/settings.py` or `src/zer0/db/` deletion (accidental) | Phase 2 test will catch immediately (import fails). |
| CLI references in docs remain | Phase 4 drift audit will flag. |
| `POST /leads/{id}/trigger-followup` scope unclarified | User decision required before Phase 3b. |
| Breaking tenant workflows if we remove an API endpoint by mistake | Phase 4 drift audit flags; manual review of each removal before commit. |

---

## Ambiguities to resolve with user

1. **Phase 3b decision:** Should `POST /leads/{id}/trigger-followup` be *implemented* (Option A) or *removed from spec* (Option B)?
   - If Option A: add to implementation backlog.
   - If Option B: mark as removed-by-decision with justification.

2. **Phase 1 choice:** Completely delete `spec/product/06-cli.md` or keep a tombstone note that it was removed?

3. **Blocking endpoint naming:** Should blocking use `PATCH /leads/{id}` (current) or should there be a dedicated `POST /leads/{id}/block` endpoint (cleaner REST semantics)?

---
