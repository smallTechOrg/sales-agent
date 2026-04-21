# GitHub Copilot — Zer0

All rules are in [`spec/engineering/ai-agents.md`](../spec/engineering/ai-agents.md). Read that first.

## Copilot-specific

Scoped instructions in [`instructions/`](instructions/) auto-apply to matching paths via `applyTo` frontmatter — each is a thin pointer to a `spec/engineering/` file.

## Agents (invoke via `@<name>`)

| Agent | Purpose |
| ----- | ------- |
| `drift-auditor` | Audit spec/code drift |
| `dry-auditor` | Audit for duplicated facts |
| `link-validator` | Validate markdown links |
| `planner` | Draft a plan before multi-file edits |
| `plan-reviewer` | Review a plan before executing |
| `spec-reviewer` | Verify a change traces back to spec |

## Slash commands

| Command | Purpose |
| ------- | ------- |
| `/plan` | Dispatch planner for a described task |
| `/spec-check` | Dispatch drift-auditor |
| `/spec-new-capability` | Scaffold a new capability spec |
| `/challenge` | Grill the pending change before approval |
