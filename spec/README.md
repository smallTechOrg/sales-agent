# Astra Spec

This directory is the single source of truth for Astra. Code is a mechanical
translation of what's here. Two subfolders, two audiences:

- [`product/`](product/) — what Astra does. Read these to understand the system.
- [`engineering/`](engineering/) — how contributors and AI agents write code that matches the product. Read these before making changes.

The foundational rule — change the spec first, then code — lives in
[`engineering/spec-driven.md`](engineering/spec-driven.md). Read it before anything else.

## Product (`product/`)

1. [`product/01-vision.md`](product/01-vision.md) — what Astra is and is not
2. [`product/02-architecture.md`](product/02-architecture.md) — components, abstractions, data flow, and the layered src structure

More files will be added here as the product is redefined.

## Engineering (`engineering/`)

Rules that govern how code gets written. Every rule applies everywhere unless
its Scope line says otherwise.

- [`engineering/spec-driven.md`](engineering/spec-driven.md) — the rule: spec first, code second
- [`engineering/tech-stack.md`](engineering/tech-stack.md) — language, runtime pin, canonical libraries
- [`engineering/code-style.md`](engineering/code-style.md) — structural conventions and patterns
- [`engineering/secret-hygiene.md`](engineering/secret-hygiene.md) — how secrets enter, travel, and exit the system
- [`engineering/tenant-isolation.md`](engineering/tenant-isolation.md) — patterns that maintain tenant boundaries
- [`engineering/commits.md`](engineering/commits.md) — commit and PR hygiene

### Workflows

Repeatable procedures invoked by Claude Code commands/agents and Copilot prompts.
Change the workflow here; tool-specific files are thin pointers.

- [`engineering/workflows/spec-check.md`](engineering/workflows/spec-check.md) — audit code/spec drift
- [`engineering/workflows/spec-review.md`](engineering/workflows/spec-review.md) — review spec-code coherence on a change
- [`engineering/workflows/spec-new-capability.md`](engineering/workflows/spec-new-capability.md) — scaffold a new capability spec
- [`engineering/workflows/dry-audit.md`](engineering/workflows/dry-audit.md) — audit for facts duplicated across files
- [`engineering/workflows/plan.md`](engineering/workflows/plan.md) — draft a plan before multi-file edits
- [`engineering/workflows/plan-review.md`](engineering/workflows/plan-review.md) — staff-engineer review of a plan
- [`engineering/workflows/link-validate.md`](engineering/workflows/link-validate.md) — verify every internal markdown link resolves

### Hierarchy of authority

When guidance conflicts:

1. A rule here (engineering) overrides general convention.
2. A product spec (in `product/`) overrides a rule — if a rule's example disagrees with a product file, the product file is right and the rule needs fixing.
3. Tool-specific files (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/*`, `.claude/`, `.github/agents/`, `.github/prompts/`) contain no policy — they are pointers into this directory. Change rules here, never there.

## Document status

Every file declares a status near the top:

- **STABLE** — implemented and won't change without a version bump
- **DRAFT** — under active design, expect churn
- **EXPERIMENTAL** — implemented but may be removed

All docs are currently **DRAFT**.

## Capability template

Every file in `product/04-capabilities/` uses this structure, in order:

1. Purpose — one or two sentences. What and for whom.
2. Trigger — what event or schedule initiates this capability.
3. Behavior — numbered steps, describing observable behaviour not implementation.
4. Inputs — config keys, state reads, external data.
5. Outputs — side effects, state writes, API calls.
6. Failure modes — named failure classes and how the system responds.
7. Out of scope — explicit non-behaviours to prevent scope creep.

Use this template verbatim when adding a capability. Uniformity is what makes
the spec mechanically translatable.

## What this spec is NOT

- Not platform API documentation.
- Not user documentation — see `README.md` at repo root.
- Not implementation notes — behaviour, not chosen libraries, class names, or file
  layouts beyond what is contractually required.
- Not a roadmap — planned-but-unbuilt capabilities go in issues, not here. Only
  build what the spec says; only spec what you intend to build.
