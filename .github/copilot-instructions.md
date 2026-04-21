# GitHub Copilot entry point

You are working in a spec-driven repo. Behaviour is defined in [`spec/product/`](../spec/product/); engineering rules are in
[`spec/engineering/`](../spec/engineering/). Read [`spec/README.md`](../spec/README.md) for orientation.

When generating code, cite the spec file that authorises the behaviour. When suggesting a behavioural change, propose the spec edit first as a separate diff.

## Scoped instructions

Files in [`instructions/`](instructions/) auto-apply to matching paths via their `applyTo` frontmatter. Each is a thin pointer to the canonical rule in [`spec/engineering/`](../spec/engineering/).

- [`instructions/spec-driven.instructions.md`](instructions/spec-driven.instructions.md) — applies to `**`
- [`instructions/secret-hygiene.instructions.md`](instructions/secret-hygiene.instructions.md) — applies to `**`
- [`instructions/code-style.instructions.md`](instructions/code-style.instructions.md) — applies to `**/*.py`
- [`instructions/tenant-isolation.instructions.md`](instructions/tenant-isolation.instructions.md) — applies to `src/**`

## Custom agents

Invoke via the agent picker (`@<name>`) or as subagents. Each is defined in [`agents/`](agents/) and delegates to a canonical workflow in `spec/engineering/workflows/`.

| Agent | Purpose |
|-------|---------|
| `drift-auditor` | Audit spec/code drift — punch-list of mismatches |
| `dry-auditor` | Audit for facts stated in more than one file |
| `link-validator` | Validate every relative markdown link and anchor |
| `planner` | Draft a phase-wise gated plan in `reports/` before multi-file edits |
| `plan-reviewer` | Staff-engineer review of a plan — Proceed / Revise / Reject |
| `spec-reviewer` | Verify a change traces back to spec (coherence check) |

## Prompts (slash commands)

Invoke via `/` in chat. Each is defined in [`prompts/`](prompts/).

| Prompt | Purpose |
|--------|---------|
| `/plan` | Dispatch planner to draft a plan for a described task |
| `/spec-check` | Dispatch drift-auditor to report spec/code drift |
| `/spec-new-capability` | Scaffold a new capability spec file |
| `/challenge` | Grill the pending change with hard questions before approval |

## Cross-tool note

This repo is also configured for Claude Code via [`../CLAUDE.md`](../CLAUDE.md) and for OpenAI/Codex agents via [`../AGENTS.md`](../AGENTS.md). Canonical rules are shared — change them in [`spec/engineering/`](../spec/engineering/), never in tool-specific files.
