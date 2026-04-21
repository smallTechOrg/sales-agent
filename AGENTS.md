# Working in astra-agent

This document is for OpenAI Codex, GPT-based agents, and any coding assistant that
reads `AGENTS.md`. It shares the same canonical conventions as [`CLAUDE.md`](CLAUDE.md).

## The rule

**Spec first. Code second.**

The `spec/` directory is the single source of truth. Before writing or changing
code, write or update the relevant spec file. See [`spec/engineering/spec-driven.md`](spec/engineering/spec-driven.md).

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
    secret-hygiene.md
    tenant-isolation.md
    commits.md
    workflows/           ← repeatable procedures for agents
      spec-check.md
      spec-review.md
      spec-new-capability.md
      dry-audit.md
      plan.md
      plan-review.md
      link-validate.md
```

## Implementation shape (when code exists)

- Python 3.12, typed with Pydantic v2 + strict mypy.
- Layered architecture: `domain` (nouns) → `tools` (verbs) → `graph` (orchestration) → `cli` (edges).
- See `spec/product/02-architecture.md` for the full structure and rules.

## Workflows available

Invoke these for structured tasks:

| Task | Workflow |
| ---- | -------- |
| Multi-file change | Read `spec/engineering/workflows/plan.md` and draft a plan in `reports/` first |
| Audit spec/code drift | Follow `spec/engineering/workflows/spec-check.md` |
| Review a change for coherence | Follow `spec/engineering/workflows/spec-review.md` |
| Review a plan before executing | Follow `spec/engineering/workflows/plan-review.md` |
| Scaffold a new capability spec | Follow `spec/engineering/workflows/spec-new-capability.md` |
| Audit for duplicate facts | Follow `spec/engineering/workflows/dry-audit.md` |
| Validate markdown links | Follow `spec/engineering/workflows/link-validate.md` |

## Don't

- Don't write code before the spec is written.
- Don't add framework magic. If you can't explain the control flow in 60 seconds, it's wrong.
- Don't store secrets in code. See `spec/engineering/secret-hygiene.md`.
- Don't write async where sync works. Add async only when you have measured contention.
- Don't commit `.env` files or any file containing a secret.
