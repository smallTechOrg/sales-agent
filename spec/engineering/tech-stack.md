# Tech Stack

**Scope:** entire repository.

## Language and runtime

- Python 3.12 (pinned in `.tool-versions`).
- Typed with Pydantic v2 and strict mypy.

## Canonical libraries

| Concern            | Library                         |
| ------------------ | ------------------------------- |
| Data models        | `pydantic>=2.8`                 |
| Settings / secrets | `pydantic-settings>=2.4`        |
| Agent orchestration| `langgraph>=0.2`                |
| LLM client         | `anthropic>=0.40` (default)     |
| CLI                | `click>=8.1` + `rich>=13.7`     |
| HTTP               | `httpx>=0.27`                   |
| Structured logging | `structlog>=24.1`               |

## What NOT to use

- No framework magic on top of LangGraph. If you can't explain the control flow
  in 60 seconds, it's wrong.
- No async where sync works. Add async only when you have measured contention.
- No secrets in code. Use `.env` via `pydantic-settings`.
