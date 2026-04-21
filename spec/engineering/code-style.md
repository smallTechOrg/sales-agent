# Code Style

**Scope:** entire repository.

## Structural conventions

- Every module boundary: Pydantic models in, Pydantic models out. Never raw dicts.
- Tools are pure-ish functions: one input model, one output model, no hidden state.
- Prompts live in `src/zer0/prompts/` as `.md` files. Never inline strings in Python.
- The graph (`graph/agent.py`) stays under ~50 lines. Behaviour lives in nodes and tools.
- Every tool call logs via `observability`. No silent actions.

## File layout conventions

| You want to...                   | Put it in...                   |
| -------------------------------- | ------------------------------ |
| Add a new tool                   | `src/zer0/tools/<name>.py`    |
| Add a new data model             | `src/zer0/domain/<name>.py`   |
| Change the agent control flow    | `src/zer0/graph/agent.py`     |
| Change what the planner decides  | `src/zer0/prompts/system.md`  |
| Add an eval case                 | `tests/evals/cases.jsonl`      |

## Naming

- Pydantic models: `PascalCase` nouns (`Lead`, `Research`, `Email`).
- Tool functions: `snake_case` verbs (`research_lead`, `draft_email`).
- Node functions (graph): `snake_case` verbs prefixed with `node_` (`node_plan`, `node_call_tool`).

## Testing

Every tool and every node must have a unit test. If it's not covered, assume it
doesn't work.
