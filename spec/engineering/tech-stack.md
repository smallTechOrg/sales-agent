# Tech Stack

**Scope:** entire repository.

## Language and runtime

- Python 3.12 (pinned in `.tool-versions`).
- Typed with Pydantic v2 and strict mypy.

## Canonical libraries

| Concern            | Library                              |
| ------------------ | ------------------------------------ |
| Data models        | `pydantic>=2.8`                      |
| Settings / secrets | `pydantic-settings>=2.4`             |
| Agent orchestration| `langgraph>=0.2`                     |
| LLM client         | `google-genai>=1.0`                  |
| CLI                | `click>=8.1` + `rich>=13.7`          |
| HTTP               | `httpx>=0.27`                        |
| Structured logging | `structlog>=24.1`                    |
| API framework      | `fastapi>=0.115` + `uvicorn>=0.30`   |
| Database ORM       | `sqlalchemy>=2.0` (sync, psycopg3)   |
| Migrations         | `alembic>=1.13`                      |
| Scheduler          | `apscheduler>=3.10`                  |
| Search             | `tavily-python>=0.3` (Tavily web search, optional key), `duckduckgo-search>=6.0` (no key required) |

## What NOT to use

- No framework magic on top of LangGraph. If you can't explain the control flow
  in 60 seconds, it's wrong.
- No async where sync works. Add async only when you have measured contention.
- No secrets in code. Use `.env` via `pydantic-settings`.
