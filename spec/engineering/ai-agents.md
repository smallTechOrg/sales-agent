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

## 8. Keeping tool files in sync

`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.claude/` are integration shims. They must never contain rules. If you need to add or change a rule, add it here in `spec/engineering/ai-agents.md` (or another `spec/engineering/` file) and update the pointer in the shim if needed. The shims stay lean — they exist only so each tool can find this file.
