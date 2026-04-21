# Zer0 Spec

This directory is the single source of truth for Zer0. Code is a mechanical
translation of what's here. Two subfolders, two audiences:

- [`product/`](product/) — what Zer0 does. Read these to understand the system.
- [`engineering/`](engineering/) — how contributors and AI agents write code that matches the product. Read these before making changes.

The foundational rule — change the spec first, then code — lives in
[`engineering/spec-driven.md`](engineering/spec-driven.md). Read it before anything else.

## Product (`product/`)

Read in order:

1. [`product/01-vision.md`](product/01-vision.md) — what Zer0 is and is not
2. [`product/02-architecture.md`](product/02-architecture.md) — components, abstractions, data flow, module dependency graph
3. [`product/03-tenancy.md`](product/03-tenancy.md) — the multi-tenant model, isolation guarantees, credential lifecycle
4. [`product/04-capabilities/`](product/04-capabilities/) — one file per discrete behaviour (discovery, enrichment, qualification, outreach, follow-up, reply handling)
5. [`product/05-config.md`](product/05-config.md) — config hierarchy: env bootstrap → DB campaign config → `ResolvedConfig`
6. [`product/06-cli.md`](product/06-cli.md) — CLI command surface (`zer0` command group)
7. [`product/07-data-model.md`](product/07-data-model.md) — full PostgreSQL schema: tables, columns, constraints, indexes
8. [`product/08-prompts.md`](product/08-prompts.md) — LLM prompt contracts, variable lists, validation
9. [`product/09-api.md`](product/09-api.md) — REST API contract: endpoints, request/response shapes, auth, error codes
10. [`product/10-agent-graph.md`](product/10-agent-graph.md) — LangGraph design: state schema, nodes, edges, checkpointing

## Engineering (`engineering/`)

Rules that govern how code gets written. Every rule applies everywhere unless
its Scope line says otherwise.

- [`engineering/spec-driven.md`](engineering/spec-driven.md) — the rule: spec first, code second
- [`engineering/phases.md`](engineering/phases.md) — **phased implementation model**: 10 dependency-ordered phases, each with gate tests. Read before writing any code.
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
