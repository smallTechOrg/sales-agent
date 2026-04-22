# Configuration

**Status:** DRAFT

Zer0 uses a two-tier config model. Settings needed at process startup (database URL, encryption key, API keys) are environment variables. All tenant- and campaign-level configuration is stored in PostgreSQL and managed via the API or UI.

---

## Overview

```mermaid
graph TD
    ENV["config/.env<br/>(bootstrap only)"] --> Settings
    Settings --> DB["PostgreSQL<br/>(campaign config)"]
    DB --> Resolver["ConfigResolver<br/>resolve(campaign_id, tenant_id)"]
    Resolver --> RC["ResolvedConfig<br/>(runtime snapshot)"]
    RC --> Graph["LangGraph agent run"]
```

---

## File layout

```
config/
└── .env     # Bootstrap secrets only
```

All campaign/tenant config and credentials live in the DB. There are no YAML files.

---

## `config/.env` — bootstrap secrets

Gitignored. One flat file, `KEY=value`. All vars use the `ZER0_` prefix.

```dotenv
ZER0_DATABASE_URL=postgresql://zer0:zer0@localhost:5432/zer0
ZER0_LLM_PROVIDER=gemini
ZER0_GEMINI_API_KEY=AIza-...
ZER0_CREDENTIAL_ENCRYPTION_KEY=<base64-urlsafe-32-bytes>
ZER0_JWT_SECRET=<random-string>
ZER0_TAVILY_API_KEY=tvly-...
# optional overrides
ZER0_LLM_MODEL=gemini-2.0-flash
ZER0_LLM_MAX_TOKENS=4096
```

`ZER0_DATABASE_URL` is the single DB configuration point. All processes read it from here.

`ZER0_CREDENTIAL_ENCRYPTION_KEY` is a Fernet key used to encrypt tenant credentials at rest. Changing it invalidates all stored credentials.

---

## Settings model

`src/zer0/config/settings.py` — `Settings` (pydantic-settings, `env_prefix = "ZER0_"`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `database_url` | `str` | yes | PostgreSQL DSN |
| `llm_provider` | `str` | no | Default: `gemini` |
| `credential_encryption_key` | `str` | yes | Fernet key for tenant secrets |
| `jwt_secret` | `str` | yes | JWT signing secret |
| `tavily_api_key` | `str` | yes | Tavily search key |
| `gemini_api_key` | `str` | yes | Gemini API key |
| `llm_max_tokens` | `int` | no | Default: `4096` |

---

## Config resolution

`ConfigResolver.resolve(campaign_id, tenant_id) → ResolvedConfig` merges in priority order:

```
CampaignRow overrides  (highest priority)
     ↓
OfferingRow defaults
     ↓
TenantRow credentials  (injected from encrypted columns)
     ↓
Settings defaults      (lowest priority)
```

```mermaid
sequenceDiagram
    participant Node as node_resolve_config
    participant CR as ConfigResolver
    participant DB

    Node->>CR: resolve(campaign_id, tenant_id)
    CR->>DB: SELECT campaigns WHERE id=campaign_id AND tenant_id
    DB-->>CR: CampaignRow
    CR->>DB: SELECT offerings WHERE id=campaign.offering_id AND tenant_id
    DB-->>CR: OfferingRow
    CR->>DB: SELECT tenants WHERE id=tenant_id
    DB-->>CR: TenantRow (encrypted creds)
    CR->>CR: Fernet.decrypt(cred_bytes)
    CR-->>Node: ResolvedConfig
```

---

## Tenant credentials (in DB, encrypted)

Stored as Fernet-encrypted bytes in the `tenants` table:

| Column | Plaintext value |
|---|---|
| `google_oauth_token_enc` | Gmail OAuth token JSON blob |
| `whatsapp_api_key_enc` | Meta Cloud API key |
| `slack_webhook_url` | Slack webhook URL (plaintext — not a credential) |

The `ConfigResolver._decrypt_optional(value)` helper decrypts using `ZER0_CREDENTIAL_ENCRYPTION_KEY`. Returns `None` if value is `None` or decryption fails (logs warning).

---

## Config validation

At graph startup (`node_resolve_config`):

1. Campaign exists and belongs to the given `tenant_id`.
2. Offering exists and belongs to the same `tenant_id`.
3. Required fields (`icp`, `qualification_config`, `outreach_config`) are non-null.
4. At least one discovery source is enabled.

Validation failure emits `config_validation_failed` and transitions to `node_handle_error`.

---

## Deleted config surface

These patterns are **not used** in Zer0:

- `tenant.yaml` files — no YAML config files at all
- Plaintext API keys in environment variables aside from bootstrap vars
- Hardcoded model names or thresholds in Python source
