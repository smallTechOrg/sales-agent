# Architecture

Status: DRAFT

> The high-level product architecture will be defined here. The layered src
> structure below is the proven implementation skeleton — any rebuild should
> follow it.

## Layered src structure

The implementation follows a strict four-layer model. Each layer has a single
responsibility and only depends on layers below it.

```
┌──────────────────────────────────────────────┐
│                    CLI                       │  ← click, rich (humans only)
├──────────────────────────────────────────────┤
│                   GRAPH                      │  ← langgraph: state, nodes, edges
├──────────────────────────────────────────────┤
│    TOOLS         │    LLM      │   MEMORY    │  ← typed functions / providers
├──────────────────────────────────────────────┤
│              DOMAIN MODELS                   │  ← pydantic: business nouns
└──────────────────────────────────────────────┘
```

### Module responsibilities

| Module           | Responsibility                                                  |
| ---------------- | --------------------------------------------------------------- |
| `domain/`        | Pydantic models for every business noun.                        |
| `tools/`         | Typed functions the agent can call.                             |
| `llm/`           | Model client + the tool JSON schemas the planner sees.          |
| `graph/`         | State, nodes, conditional edges, compiled runtime.              |
| `memory/`        | Checkpointing.                                                  |
| `prompts/`       | Markdown files loaded at runtime — never inlined in Python.     |
| `observability/` | Structured logs + console tracer.                               |
| `cli/`           | Click commands — the edge of the system.                        |
| `config/`        | pydantic-settings, loaded from `.env`.                          |

### Implementation rules derived from this structure

1. Types at every boundary. Any function that crosses a module boundary takes and
   returns Pydantic models — never raw dicts.
2. Tools are pure-ish functions. A tool takes a Pydantic input, returns a Pydantic
   output, and logs via the `observability` module. No hidden state.
3. The graph is thin. `graph/agent.py` should stay under ~50 lines. All behavior
   lives in node functions and tool functions.
4. Prompts are data. They live in `prompts/` as markdown, loaded at runtime.
5. Secrets via settings. Use `.env` via `pydantic-settings`. Never hard-code.

## Control flow

> To be defined — the specific agent loop and data flow for this product.

## Component diagram

> To be defined.

## Data flow

> To be defined.
