# Claude Code — Zer0

All rules are in [`spec/engineering/ai-agents.md`](spec/engineering/ai-agents.md). Read that first.

## Claude-specific

- Subagents and slash commands are defined in [`.claude/`](.claude/).
- Use the `planner` subagent before any multi-file change.
- Use the `drift-auditor` subagent to check spec/code drift.
