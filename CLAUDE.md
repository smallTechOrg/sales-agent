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

## Don't

- Don't write code before the spec is written.
- Don't add framework magic. If you can't explain the control flow in 60 seconds, it's wrong.
- Don't store secrets in code. Use `.env` via `pydantic-settings`.
- Don't write async where sync works. Add async only when you have measured contention.
