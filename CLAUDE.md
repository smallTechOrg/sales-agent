# Working in astra-agent with Claude

This document is for Claude (or any coding assistant) working inside this repo. It captures
the conventions we expect to be followed.

## The rule

**Spec first. Code second.**

The `spec/` directory is the single source of truth. Before writing or changing
code, write or update the relevant spec file. See `spec/engineering/spec-driven.md`.

## Spec layout

```
spec/
  README.md              ← start here
  product/               ← what the system does
    01-vision.md
    02-architecture.md   ← includes the layered src structure
  engineering/           ← how contributors write code
    spec-driven.md
    tech-stack.md
    code-style.md
```

## Implementation shape (when code exists)

- Python 3.12, typed with Pydantic v2 + strict mypy.
- Layered architecture: `domain` (nouns) → `tools` (verbs) → `graph` (orchestration) → `cli` (edges).
- See `spec/product/02-architecture.md` for the full structure and rules.

## Git workflow

Canonical rules: [`spec/engineering/commits.md`](spec/engineering/commits.md). Short version:

1. **Commit every logical unit of work.** Don't accumulate. When a task is done, commit it.
2. **Every commit goes on a feature branch** — never directly to `main`.
3. **Every feature branch must have an open PR** before the session ends.
4. **When the change touches behaviour, update the spec first.** Spec and code travel in the same commit. See [`spec/engineering/spec-driven.md`](spec/engineering/spec-driven.md).
5. Commit message subject: ≤70 chars, imperative mood. Body explains why; references the spec file that authorises the change.
6. PR body: Summary (2–3 bullets) + Test plan checklist + spec file(s) affected.

## Don't

- Don't write code before the spec is written or updated.
- Don't add framework magic. If you can't explain the control flow in 60 seconds, it's wrong.
- Don't store secrets in code. Use `.env` via `pydantic-settings`.
- Don't write async where sync works. Add async only when you have measured contention.
- Don't leave changes uncommitted at the end of a session.
- Don't push directly to `main`.
- Don't let CLAUDE.md, AGENTS.md, and `.github/copilot-instructions.md` drift from each other. If you update the git workflow or spec rules in one, update all three.
