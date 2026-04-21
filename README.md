# Astra — a sales agent, built from scratch

> A teaching repo for the **AI For Leaders: Building Agents from Scratch** workshop (v0.1).
>
> Astra is a small, honest, production-shaped sales agent. It researches a lead, drafts a
> personalized outreach email, and logs the activity — all by iterating on the classic agent
> loop: **observe → plan → act → reflect**.

---

## Why this repo exists

The workshop promises: *"You leave with a running agent you can extend tomorrow."* This is that
agent. It is intentionally:

- **Tiny** — fewer than ~600 lines of Python in `src/`.
- **Typed** — Pydantic models at every boundary; your LLM can't hand you mush.
- **Observable** — every node, every tool call is traced.
- **Replaceable** — swap Claude for another model, swap SQLite for Postgres, without touching
  the graph.

We chose **LangGraph** because it makes the agent loop explicit instead of hiding it behind
magic. You will see the nodes. You will see the edges. You will see the state.

---

## Quick start

```bash
# 1. Python 3.12 (uses .tool-versions, asdf-friendly)
python --version

# 2. Install
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# ...then paste your ANTHROPIC_API_KEY into .env

# 4. Run
astra run --lead demo
```

You should see the agent plan, call three tools, reflect, and finish — all in the terminal,
all traced.

---

## Repo layout

```
astra-agent/
├── src/astra/
│   ├── cli/            # Click-based CLI entrypoint (`astra run`, `astra leads`, ...)
│   ├── config/         # pydantic-settings — env + YAML
│   ├── domain/         # Lead, Email, Activity, Research — the nouns of the business
│   ├── llm/            # Claude client + tool schema generation
│   ├── tools/          # research_lead, draft_email, log_to_crm
│   ├── graph/          # LangGraph: state + nodes + the compiled agent
│   ├── memory/         # short-term + long-term (checkpointer)
│   ├── prompts/        # system + planner + reflector prompts (markdown)
│   └── observability/  # structured logs + trace helpers
├── tests/              # pytest — unit + integration
├── spec/               # product + tech docs (spec-driven style)
├── pyproject.toml
├── .tool-versions
├── CLAUDE.md           # how to work in this repo with Claude
└── README.md           # you are here
```

---

## The agent, in one picture

```
        ┌─────────┐
        │  START  │  <── goal + lead_id
        └────┬────┘
             ▼
        ┌─────────┐        conditional edge
        │  PLAN   │ ──────────────────────────┐
        └────┬────┘                           │
             │ tool call                      │
             ▼                                │
       ┌───────────┐                          │
       │ research_ │                          │
       │ draft_   │─── result ──► back to PLAN│
       │ log_to_  │                           │
       └───────────┘                          │
                                              ▼
                                        ┌─────────┐
                                        │ REFLECT │──► END
                                        └─────────┘
```

- **PLAN** is the brain (the model, given a planner prompt).
- **Tools** are the hands (`research_lead`, `draft_email`, `log_to_crm`).
- **REFLECT** is the boss (verifies the goal was met).

---

## Commands

| Command                 | What it does                                           |
| ----------------------- | ------------------------------------------------------ |
| `astra run --lead X`    | Run the full agent against lead `X`.                   |
| `astra leads`           | List the sample leads shipped with the repo.           |
| `astra eval`            | Run the eval suite in `tests/evals`.                   |
| `astra trace view <id>` | Pretty-print a stored trace.                           |

---

## Extending Astra

Four extensions you'll likely want in the first week:

1. **Plug in your CRM.** Implement `astra.tools.crm.get_lead` / `write_activity` against your
   real backend. No graph changes needed.
2. **Add a guardrail.** In `src/astra/graph/nodes.py`, gate `log_to_crm` behind a human
   approval. There's a `DRY_RUN` env flag wired for exactly this.
3. **Swap the model.** `astra.llm.client.get_client()` returns a provider-agnostic interface.
4. **Write evals.** Add `(lead_id, expected)` pairs under `tests/evals/cases.jsonl` and run
   `astra eval`.

---

## The 7-day plan

See [`spec/07-seven-day-plan.md`](spec/07-seven-day-plan.md). It's the exact sequence of
changes that turns this demo into a pilot in a week.

---

## License

Proprietary. For workshop participants only.
