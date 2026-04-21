# AI Agent Instructions

**Scope:** all AI coding assistants working in this repository (Claude Code, GitHub Copilot, OpenAI/Codex agents, and any future tool).

This is the single source of truth for how AI agents should behave in this repo. Tool-specific entry points (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.claude/`) are thin integration shims that point here — they contain no rules of their own.

---

## 1. Product

This is **Zer0** — an autonomous multi-tenant sales agent platform. Before writing anything, read:

- [`spec/product/01-vision.md`](../product/01-vision.md) — what Zer0 is, the four-stage loop, and success criteria.
- [`spec/product/02-architecture.md`](../product/02-architecture.md) — layered architecture, domain models, tools, config resolution.

---

## 2. Spec first

Rule: [`spec/engineering/spec-driven.md`](spec-driven.md)

- Before writing or changing code, write or update the relevant spec file.
- If there is no spec file for what you are building, create one.
- Spec and code changes travel in the same commit.
- Drift between spec and code is a bug. The spec wins.

---

## 3. Git workflow

Rule: [`spec/engineering/commits.md`](commits.md)

- Commit every logical unit of work. Do not accumulate uncommitted changes.
- Every commit goes on a feature branch — never directly to `main`.
- Every feature branch must have an open PR before the session ends.
- Commit message: ≤70 char subject, imperative mood, body references the spec file that authorises the change.
- PR body: Summary (2–3 bullets) + Test plan checklist + spec file(s) affected.

### Mandatory commit checkpoints — non-negotiable

An AI agent **must** commit and push at **each** of the following moments. Not at the end of the session. At each checkpoint, with no exceptions:

| Checkpoint | What to do |
| ---------- | ---------- |
| After completing any spec change | `git add <spec files> && git commit` immediately. |
| After completing any code change | `git add <src files> && git commit` immediately. |
| After completing a task that was in the todo list | Mark the todo completed **and** commit before moving to the next todo. |
| Before responding to the user after completing work | Verify with `git status` that the working tree is clean. If it is not, commit before replying. |
| Before the session ends | `git push origin <branch>` — branch must be on the remote. |

**The working tree must be clean before any user-facing reply that describes completed work.** If `git status` shows modified or untracked files that represent completed work, that is a bug in the agent's behaviour — fix it by committing before replying.

This rule exists because leaving uncommitted work in the tree means the work is lost if the session is interrupted, and it misleads the user about the state of the repository.

---

## 4. Code style

Rule: [`spec/engineering/code-style.md`](code-style.md)

- Python 3.12, Pydantic v2, strict mypy.
- Types at every module boundary — no raw dicts crossing layers.
- Tools are pure-ish functions: typed input → typed output → log via `observability`.
- Prompts live in `src/zer0/prompts/` as `.md` files with `{{variable}}` placeholders. Never inline in Python.
- The graph is thin — `graph/agent.py` ≤ 50 lines. All behaviour in node and tool functions.

---

## 5. Secret hygiene

Rule: [`spec/engineering/secret-hygiene.md`](secret-hygiene.md)

- No secrets in code. Use `.env` via `pydantic-settings`.
- Never commit `.env` or any file containing a credential.

---

## 6. Tenant isolation

Rule: [`spec/engineering/tenant-isolation.md`](tenant-isolation.md)

- `tenant_id` is non-nullable on every database table.
- Every query, tool call, and log entry is scoped to a tenant.
- No data crosses tenant boundaries.
- `ConfigResolver` merges Campaign overrides onto Offering defaults — no node or tool reads raw config models directly.

---

## 7. Workflows (for structured tasks)

| Task | Workflow |
| ---- | -------- |
| Multi-file change | [`spec/engineering/workflows/plan.md`](workflows/plan.md) |
| Audit spec/code drift | [`spec/engineering/workflows/spec-check.md`](workflows/spec-check.md) |
| Review a change for coherence | [`spec/engineering/workflows/spec-review.md`](workflows/spec-review.md) |
| Review a plan before executing | [`spec/engineering/workflows/plan-review.md`](workflows/plan-review.md) |
| Scaffold a new capability spec | [`spec/engineering/workflows/spec-new-capability.md`](workflows/spec-new-capability.md) |
| Audit for duplicate facts | [`spec/engineering/workflows/dry-audit.md`](workflows/dry-audit.md) |
| Validate markdown links | [`spec/engineering/workflows/link-validate.md`](workflows/link-validate.md) |

---

## 8. Phased implementation

Rule: [`spec/engineering/phases.md`](phases.md)

Every implementation — initial build, new capability, refactor — follows the 10-phase model ordered by the module dependency graph. The non-negotiable rules:

- **Never skip a phase.** Build and test each layer before the layer above it.
- **Gate before proceeding.** The gate tests for a phase must be green before writing code in the next phase.
- **Tests travel with code.** A commit adding a source file without its matching test file fails the gate. No exceptions.
- **One commit per phase.** Subject prefix: `phase-N:` (e.g. `phase-1: domain models + tests`).
- **Backfill when out of order.** If a module was implemented without tests (e.g. a bulk implementation), the next PR must add the missing phase tests before any new dependent code is added.

Phase ordering (dependency-first):

| Phase | Module | Depends on |
|---|---|---|
| 0 | Skeleton + tooling | — |
| 1 | `domain/` | 0 |
| 2 | `config/` | 1 |
| 3 | `observability/` | 1 |
| 4 | `llm/` + `prompts/` | 2 |
| 5 | `db/` | 1, 2 |
| 6 | `tools/` | 1, 3, 4 |
| 7 | `graph/` | 1, 3, 4, 5, 6 |
| 8 | `api/` | 1, 5, 7 |
| 9 | `cli/` | 2, 5, 7 |
| 10 | Integration | all |
| 11 | `ui/` (Next.js dashboard) | 8 |

---

## 9. Keeping tool files in sync

`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.claude/` are integration shims. They must never contain rules. If you need to add or change a rule, add it here in `spec/engineering/ai-agents.md` (or another `spec/engineering/` file) and update the pointer in the shim if needed. The shims stay lean — they exist only so each tool can find this file.
