# CLI

**Status:** DRAFT

The CLI is the operator interface for local dev, admin tasks, and debugging. All commands use the `zer0` entry point.

---

## Global flags

| Flag | Effect |
|---|---|
| `--config-dir PATH` | Override `config/` root. Default: `./config` relative to cwd |
| `--json-log` | Emit structured JSON logs instead of coloured console output |
| `-v` | Increase log verbosity to DEBUG |

---

## Command surface

### `zer0 version`

Prints `zer0 x.y.z`.

Exit codes: `0` success.

---

### `zer0 tenant`

#### `zer0 tenant list`

Prints all tenants with their status.

```
ID                           NAME              ENABLED  CAMPAIGNS  STATUS
acme-corp                    Acme Corporation  yes      3          ok
beta-inc                     Beta Inc          yes      1          degraded
draft-client                 Draft Client      no       0          -
```

#### `zer0 tenant add <id> [--name "Display Name"]`

Inserts a `tenants` row. Starts `enabled = false`. Fails if ID already exists.

Exit codes: `0` created; `1` duplicate.

#### `zer0 tenant enable <id>` / `zer0 tenant disable <id>`

Updates `tenants.enabled`. Warns that a daemon restart is needed.

Exit codes: `0` updated; `1` not found.

#### `zer0 tenant remove <id> [--force]`

Cascade-deletes all rows scoped to `tenant_id`. Prompts for confirmation unless `--force`.

Exit codes: `0` removed; `1` not found.

---

### `zer0 campaign run <campaign_id>`

Triggers `runner.run_campaign(campaign_id, tenant_id)` synchronously.

```
zer0 campaign run abc-123 --tenant acme-corp
```

Useful for manual testing and one-off backfills. Output mirrors graph node progression.

Exit codes: `0` completed; `1` campaign not found; `2` runtime error.

---

### `zer0 health [--tenant <id>]`

Checks each configured service.

```
Operator
  Database:       ok
  LLM (gemini):   ok

Tenant: acme-corp
  Gmail:         ok
  WhatsApp:      FAILED — missing credential WHATSAPP_API_KEY
  Slack:         ok
```

Exit codes: `0` all ok; `1` not found; `2` one or more FAILED.

---

### `zer0 events --tenant <id> [--limit N]`

Lists recent events for a tenant.

```
ID    TIME           TYPE              CAMPAIGN
42    2m ago         lead_discovered   campaign-abc
41    1h ago         lead_qualified    campaign-abc
40    3h ago         message_sent      campaign-abc
```

Exit codes: `0` success; `1` tenant not found.

---

### `zer0 config show`

Prints current `Settings` values. Secret fields are masked (`***`).

```
ZER0_DATABASE_URL:              postgresql://zer0:***@localhost/zer0
ZER0_GEMINI_API_KEY:            ***
ZER0_LLM_PROVIDER:              gemini
ZER0_LLM_MODEL:                 gemini-2.0-flash
ZER0_LLM_MAX_TOKENS:            4096
ZER0_TAVILY_API_KEY:            ***
ZER0_CREDENTIAL_ENCRYPTION_KEY: ***
ZER0_JWT_SECRET:                ***
```

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Operator error (bad args, not found, duplicate) |
| `2` | Runtime error (external service failure, DB error) |
| `3` | Validation error (config invalid, schema error) |

---

## What's not here (explicitly out of scope for v1)

- `zer0 prompt edit` — use the API or direct DB.
- `zer0 tenant rename` — IDs are immutable; remove and re-add.
- `zer0 campaign approve` — approval is done via the API (`POST /api/v1/approvals`).
