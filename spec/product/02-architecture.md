# Architecture

Status: DRAFT

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

| Module           | Responsibility                                                                 |
| ---------------- | ------------------------------------------------------------------------------ |
| `domain/`        | Pydantic models for every business noun (Lead, Company, OutreachMessage, etc.) |
| `tools/`         | Typed functions the agent can call — one file per tool.                        |
| `llm/`           | Model client + tool JSON schemas the planner sees.                             |
| `graph/`         | State, nodes, conditional edges, compiled runtime.                             |
| `memory/`        | Checkpointing — persists loop state across runs.                               |
| `prompts/`       | Markdown files loaded at runtime — never inlined in Python.                    |
| `observability/` | Structured logs + console tracer.                                              |
| `cli/`           | Click commands — the edge of the system.                                       |
| `config/`        | pydantic-settings, loaded from `.env`.                                         |

## Control flow

The agent runs a continuous loop over the four stages. Each stage is a node in the LangGraph graph. Edges are conditional: a lead that fails qualification never reaches outreach.

```
            ┌─────────────┐
            │  planner    │  ← decides next action given loop state
            └──────┬──────┘
                   │
       ┌───────────▼───────────┐
       │       discover        │  ← web search, directory scrape → RawLead list
       └───────────┬───────────┘
                   │  (for each lead)
       ┌───────────▼───────────┐
       │       research        │  ← enrich company + contact → EnrichedLead
       └───────────┬───────────┘
                   │
       ┌───────────▼───────────┐
       │       qualify         │  ← score against ICP rubric → QualifiedLead | Rejected
       └───────────┬───────────┘
                   │  (qualified only)
       ┌───────────▼───────────┐
       │       outreach        │  ← draft + send personalised email → SentMessage
       └───────────┬───────────┘
                   │
            ┌──────▼──────┐
            │  checkpoint │  ← persist state, loop or halt
            └─────────────┘
```

## Domain models

| Model            | Fields (key)                                                         |
| ---------------- | -------------------------------------------------------------------- |
| `ICP`            | target_industries, target_roles, company_size_range, keywords        |
| `RawLead`        | name, company, url, source                                           |
| `EnrichedLead`   | all RawLead fields + company_summary, role_summary, recent_signals   |
| `QualifiedLead`  | EnrichedLead + score (0–100), rationale                              |
| `RejectedLead`   | EnrichedLead + rejection_reason                                      |
| `OutreachDraft`  | lead_id, subject, body, personalisation_notes                        |
| `SentMessage`    | OutreachDraft + sent_at, message_id                                  |

## Tools

| Tool                  | Input            | Output                          | Notes                                      |
| --------------------- | ---------------- | ------------------------------- | ------------------------------------------ |
| `web_search`          | query string     | list of URLs + snippets         | Wraps a search API (e.g. Tavily, Serper).  |
| `scrape_page`         | URL              | cleaned page text               | Extracts readable content from a webpage.  |
| `find_contact`        | company URL      | name, email, role               | Finds decision-makers at a company.        |
| `enrich_lead`         | RawLead          | EnrichedLead                    | Combines scrape + LLM summarisation.       |
| `qualify_lead`        | EnrichedLead     | QualifiedLead \| RejectedLead   | Scores against ICP using LLM + rubric.     |
| `draft_outreach`      | QualifiedLead    | OutreachDraft                   | Generates personalised email via LLM.      |
| `send_email`          | OutreachDraft    | SentMessage                     | Sends via SMTP or transactional API.       |

## Prompts

| File                       | Purpose                                              |
| -------------------------- | ---------------------------------------------------- |
| `prompts/planner.md`       | System prompt for the top-level planning node.       |
| `prompts/researcher.md`    | Instructions for the research node.                  |
| `prompts/qualifier.md`     | ICP rubric + scoring instructions.                   |
| `prompts/outreach.md`      | Tone, format, and personalisation rules for emails.  |

## Data flow

```
CLI (icp.json + config)
  → graph/agent.py (loop state)
    → discover node  → [RawLead, ...]
    → research node  → [EnrichedLead, ...]
    → qualify node   → [QualifiedLead, ...] + [RejectedLead, ...]
    → outreach node  → [SentMessage, ...]
  → memory/checkpoint (persisted state)
  → observability (structured logs)
```

## Implementation rules

1. Types at every boundary. Any function that crosses a module boundary takes and returns Pydantic models — never raw dicts.
2. Tools are pure-ish functions. A tool takes a Pydantic input, returns a Pydantic output, and logs via `observability`. No hidden state.
3. The graph is thin. `graph/agent.py` stays under ~50 lines. All behaviour lives in node functions and tool functions.
4. Prompts are data. They live in `prompts/` as markdown, loaded at runtime.
5. Secrets via settings. Use `.env` via `pydantic-settings`. Never hard-code.
