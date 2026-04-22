# GitHub Copilot — Zer0

All rules are in [`spec/engineering/ai-agents.md`](../spec/engineering/ai-agents.md). Read that first.

## Mandatory spec reads — every session

Before responding to any coding task, you **must** have read every file listed in
[`instructions/spec-files.instructions.md`](instructions/spec-files.instructions.md)
in full during the current session — from disk, not from a summary or conversation history.

The full manifest and the rule are in `spec/engineering/ai-agents.md` §2 ("Mandatory spec manifest").  
A summarised spec is **not** a spec. If your context window holds only a paraphrase of a spec file, re-read it.

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
