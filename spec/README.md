# Astra Spec

This directory is the single source of truth for Astra. Code is a mechanical
translation of what's here. Two subfolders, two audiences:

- `product/` — what Astra does. Read these to understand the system.
- `engineering/` — how contributors and AI agents write code that matches the product. Read these before making changes.

The foundational rule — change the spec first, then code — lives in
`engineering/spec-driven.md`. Read it before anything else.

## Product (`product/`)

First pass, in order:

1. `product/01-vision.md` — what Astra is and is not
2. `product/02-architecture.md` — components, abstractions, data flow, and the layered src structure

More files will be added here as the product is redefined.

## Engineering (`engineering/`)

Rules that govern how code gets written. Every rule applies everywhere unless
its Scope line says otherwise.

- `engineering/spec-driven.md` — the rule: spec first, code second
- `engineering/tech-stack.md` — language, runtime pin, canonical libraries
- `engineering/code-style.md` — structural conventions and patterns

## Document status

Every file declares a status near the top:

- **STABLE** — implemented and won't change without a version bump
- **DRAFT** — under active design, expect churn
- **EXPERIMENTAL** — implemented but may be removed

All docs are currently **DRAFT**.

## What this spec is NOT

- Not platform API documentation.
- Not user documentation — see `README.md` at repo root.
- Not implementation notes — behaviour, not chosen libraries, class names, or file
  layouts beyond what is contractually required.
- Not a roadmap — planned-but-unbuilt capabilities go in issues, not here.
