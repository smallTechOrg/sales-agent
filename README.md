# Zer0 — autonomous sales agent platform

Zer0 is a **multi-tenant autonomous sales agent** that runs the entire top-of-funnel pipeline — cold prospecting to first positive reply — without human intervention. Tenants configure everything via a web dashboard; the agent discovers, researches, qualifies, and outreaches on its own.

See [`spec/product/01-vision.md`](spec/product/01-vision.md) for the full product description.

---

## Quick start

```bash
# 1. Python 3.12 (pinned in .tool-versions, asdf-friendly)
python --version  # should print 3.12.x

# 2. Install
pip install -e ".[dev]"

# 3. Configure — copy the example and fill in required values
cp .env.example .env
# Required: ZER0_DATABASE_URL, ZER0_ANTHROPIC_API_KEY, ZER0_TAVILY_API_KEY,
#           ZER0_JWT_SECRET, ZER0_CREDENTIAL_ENCRYPTION_KEY

# 4. Run database migrations
alembic upgrade head

# 5. Start the API server
uvicorn zer0.api:app --reload

# 6. Or run the agent directly via the CLI
zer0 campaign run <campaign-id>
```

---

## Repo layout

```
sales-agent/
├── src/zer0/
│   ├── api/            # FastAPI routers — auth, tenants, offerings, campaigns,
│   │                   #   leads, approvals, messages, events
│   ├── cli/            # Click CLI — zer0 version, tenant, campaign, leads, run
│   ├── config/         # pydantic-settings (Settings) + ConfigResolver
│   ├── db/             # SQLAlchemy 2.0 ORM models + session factory
│   ├── domain/         # Pure Python domain models (no ORM, no I/O)
│   │                   #   config, lead, outreach — the nouns of the business
│   ├── graph/          # LangGraph StateGraph — state, nodes, edges, agent
│   ├── llm/            # Anthropic Claude client + prompt loader
│   ├── observability/  # structlog configuration + write_event() + Slack webhook
│   ├── prompts/        # Markdown prompt templates with {{ variable }} injection
│   └── tools/          # Agent tools — discovery, research, qualify, outreach …
├── tests/
│   ├── unit/           # per-module unit tests (phases 1–7)
│   └── integration/    # FastAPI TestClient integration tests (phase 8)
├── alembic/            # database migrations
├── spec/               # single source of truth — read before any change
├── reports/            # AI-agent planning reports
├── pyproject.toml
├── .tool-versions      # asdf — Python 3.12.x
├── CLAUDE.md           # Claude Code entry point → spec/engineering/ai-agents.md
├── AGENTS.md           # OpenAI/Codex entry point → spec/engineering/ai-agents.md
└── README.md           # you are here
```

---

## The agent pipeline

```
DISCOVER → RESEARCH → QUALIFY → OUTREACH → FOLLOW-UP
```

Each stage is a LangGraph node. Conditional edges route between stages or to an error handler.

```
START
  └─► resolve_config ──── error ──► handle_error ──► END
           │
           ▼ ok
        discover ───────── error ──► handle_error
           │ no leads ──► END
           ▼ leads
        research
           │
           ▼
        qualify ─────────── error ──► handle_error
           │ no qualified ► END
           ▼ qualified
     approval_gate ─────── error ──► handle_error
           │ pending ────► END (parked for human review)
           │ no approved ► END
           ▼ approved
        outreach
           │
           ▼
      follow_up_loop ◄──── active leads
           │ all done
           ▼
          END
```

Full graph spec: [`spec/product/10-agent-graph.md`](spec/product/10-agent-graph.md)

---

## CLI commands

| Command | What it does |
| ------- | ------------ |
| `zer0 version` | Print the installed version. |
| `zer0 tenant create` | Create a new tenant. |
| `zer0 tenant list` | List all tenants. |
| `zer0 campaign run <id>` | Trigger an immediate agent run for a campaign. |
| `zer0 campaign list` | List campaigns across all tenants. |
| `zer0 leads list` | List leads with optional filters. |

Full CLI spec: [`spec/product/06-cli.md`](spec/product/06-cli.md)

---

## Tests

```bash
pytest                   # run all tests
pytest tests/unit/       # unit tests only
pytest tests/integration # integration tests only
```

77 tests across 8 phases. The test suite follows the phased model in [`spec/engineering/phases.md`](spec/engineering/phases.md) — each phase's tests must pass before the next phase's code is written.

---

## Spec

Everything that governs what Zer0 does and how it's built lives in `spec/`. Start here:

- [`spec/README.md`](spec/README.md) — index of all spec files
- [`spec/product/01-vision.md`](spec/product/01-vision.md) — what Zer0 is
- [`spec/engineering/ai-agents.md`](spec/engineering/ai-agents.md) — rules for AI coding assistants

---

## License

Proprietary.
