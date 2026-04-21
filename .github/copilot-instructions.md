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

## Git workflow

Canonical rules: [`spec/engineering/commits.md`](../spec/engineering/commits.md). Short version:

1. **Commit every logical unit of work.** Don't accumulate. When a task is done, commit it.
2. **Every commit goes on a feature branch** — never directly to `main`.
3. **Every feature branch must have an open PR** before the session ends.
4. **When the change touches behaviour, update the spec first.** Spec and code travel in the same commit. See [`spec/engineering/spec-driven.md`](../spec/engineering/spec-driven.md).
5. Commit message subject: ≤70 chars, imperative mood. Body explains why; references the spec file that authorises the change.
6. PR body: Summary (2–3 bullets) + Test plan checklist + spec file(s) affected.

## Don't

- Don't write code before the spec is written or updated.
- Don't leave changes uncommitted at the end of a session.
- Don't push directly to `main`.
- Don't let `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md` drift from each other. If you update the git workflow or spec rules in one, update all three.

## Cross-tool note

This repo is also configured for Claude Code via [`../CLAUDE.md`](../CLAUDE.md) and for OpenAI/Codex agents via [`../AGENTS.md`](../AGENTS.md). Canonical rules live in [`spec/engineering/`](../spec/engineering/) — that is the source of truth. The git workflow section above and the Don't list must stay identical across all three files.
