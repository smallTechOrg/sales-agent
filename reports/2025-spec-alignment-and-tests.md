# Plan: Spec Alignment + Compulsory Tests

**Date:** 2025  
**Branch:** `feat/implementation`  
**Status:** APPROVED — executing

---

## Context

PR #3 (`feat/implementation`) is open with 58 files implementing all 13 tools,
the LangGraph agent, FastAPI routes, and Alembic migrations. Two gaps remain:

1. The spec structure does not mirror the reference layout (`astra-agent@feat/phase-11-release`).
2. There are zero tests — violating `spec/engineering/code-style.md` ("Every tool and every node must have a unit test").
3. A `reports/` directory was never created before multi-file changes — a rule from `spec/engineering/ai-agents.md`.

This report corrects all three.

---

## Gap table

| What | Current state | Target state |
|---|---|---|
| `spec/product/03-*` | `03-db-schema.md` | `03-tenancy.md` (new), `07-data-model.md` (renamed) |
| `spec/product/04-*` | `04-api.md` | `04-capabilities/` (new dir), `09-api.md` (renamed) |
| `spec/product/05-*` | `05-agent-graph.md` | `05-config.md` (new), `10-agent-graph.md` (renamed) |
| `spec/product/06-*` | — | `06-cli.md` (new) |
| `spec/product/08-*` | — | `08-prompts.md` (new) |
| `tests/` | Does not exist | Full unit + integration suite |
| `reports/` | Does not exist | This file |

---

## Spec renaming map

| From | To | Action |
|---|---|---|
| `spec/product/03-db-schema.md` | `spec/product/07-data-model.md` | git mv + heading update |
| `spec/product/04-api.md` | `spec/product/09-api.md` | git mv |
| `spec/product/05-agent-graph.md` | `spec/product/10-agent-graph.md` | git mv |

## New spec files

| File | Content |
|---|---|
| `spec/product/03-tenancy.md` | Multi-tenant model: isolation guarantees, lifecycle, secrets |
| `spec/product/04-capabilities/` | One file per major capability (6 files) |
| `spec/product/05-config.md` | Config hierarchy (env + DB), ZER0_ prefix, secrets |
| `spec/product/06-cli.md` | CLI surface (`zer0` command group) |
| `spec/product/08-prompts.md` | LLM prompt contracts, variable lists, validation |

---

## Test plan

### Unit tests (`tests/unit/`)

| File | What it tests |
|---|---|
| `test_smoke.py` | `__version__` is importable |
| `domain/test_models.py` | `LeadStage`, `QualifiedLead`, `OutreachDraft`, `ResolvedConfig` invariants |
| `config/test_settings.py` | `Settings` reads `ZER0_` env vars, raises on missing required |
| `config/test_resolver.py` | `ConfigResolver.resolve()` merges campaign → offering → tenant; mock db |
| `tools/test_qualify_lead.py` | Qualification scoring with mock LLM; accept/reject thresholds |
| `tools/test_detect_language.py` | Language detection returns `"en"` fallback on LLM error |
| `graph/test_edges.py` | Edge routing: after_qualify, after_approval_gate, after_follow_up_loop |

### Integration tests (`tests/integration/`)

| File | What it tests |
|---|---|
| `test_api.py` | FastAPI TestClient: health, auth token, 401 on missing auth, leads 422 on bad pagination |

---

## Phased implementation model — new requirement

`spec/engineering/phases.md` (new file) defines 10 dependency-ordered phases for all future implementation work:

| Phase | Module | Gate |
|---|---|---|
| 0 | Skeleton + tooling | `test_smoke.py` passes |
| 1 | `domain/` | Domain model tests pass |
| 2 | `config/` | Settings + resolver tests pass |
| 3 | `observability/` | Event writer tests pass |
| 4 | `llm/` + `prompts/` | Client + prompt loading tests pass |
| 5 | `db/` | ORM models importable, schema creates cleanly |
| 6 | `tools/` | Every tool has happy-path + failure test |
| 7 | `graph/` | Edge routing tested; end-to-end graph stubbed |
| 8 | `api/` | Every route has 2xx + 4xx test |
| 9 | `cli/` | Every command has exit-code test |
| 10 | Integration | Full suite passes |

`spec/engineering/ai-agents.md` section 8 references `phases.md` and lists the non-negotiable rules (no phase skipping, gate before proceeding, tests travel with code).

## Execution phases

1. ✅ Create `reports/` + this file  
2. Spec: `git mv` old files, create new files, update `spec/README.md`, add `phases.md`, update `ai-agents.md`  
3. Tests: create `tests/` directory tree with all files above  
4. Each phase committed separately with `spec:` or `test:` prefix  

---

## Risk

- Renaming spec files changes relative links in `spec/README.md` — must update together.
- Tests do not require a running Postgres; all DB-touching tests mock the session.
- Integration tests use FastAPI's `TestClient` with SQLite in-memory (overrides `DATABASE_URL`).
