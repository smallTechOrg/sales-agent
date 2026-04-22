# Claude Code — Zer0

All rules are in [`spec/engineering/ai-agents.md`](spec/engineering/ai-agents.md). Read that first.

## Claude-specific

- Subagents and slash commands are defined in [`.claude/`](.claude/).
- Use the `planner` subagent before any multi-file change.
- Use the `drift-auditor` subagent to check spec/code drift.

## Mandatory spec reads — session start

Before reading any task or writing any code, call `Read` on every file in the spec manifest defined in
`spec/engineering/ai-agents.md` §2 ("Mandatory spec manifest"). Summaries and conversation history
are **not** a substitute — re-read from disk.

Product spec files to read on every session start:

```
spec/product/01-vision.md
spec/product/02-architecture.md
spec/product/03-tenancy.md
spec/product/04-capabilities/01-discovery.md
spec/product/04-capabilities/02-enrichment.md
spec/product/04-capabilities/03-qualification.md
spec/product/04-capabilities/04-outreach.md
spec/product/04-capabilities/05-follow-up.md
spec/product/04-capabilities/06-reply-handling.md
spec/product/04-capabilities/07-contact-discovery.md
spec/product/04-capabilities/08-approval.md
spec/product/05-config.md
spec/product/06-cli.md
spec/product/07-data-model.md
spec/product/08-prompts.md
spec/product/09-api.md
spec/product/10-agent-graph.md
spec/product/11-ui-dashboard.md
```

Engineering rules (read once per session):

```
spec/engineering/ai-agents.md
spec/engineering/spec-driven.md
spec/engineering/secret-hygiene.md
spec/engineering/tenant-isolation.md
spec/engineering/code-style.md
spec/engineering/commits.md
```

A spec that was read in a prior session and then summarised does **not** count. If the current context
window contains only a summary of a spec file, re-read the file.
