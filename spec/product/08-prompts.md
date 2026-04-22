# Prompts

**Status:** DRAFT

Prompts are first-class spec artefacts, not source-code constants. They live as markdown files in `src/zer0/prompts/` and are loaded at process startup by `LLMClient.load_prompt(name, config)`. This lets tone and instructions be changed without a code deploy.

---

## Storage

Prompts are `.md` files under `src/zer0/prompts/`. Each file is a template with `{{ variable }}` placeholders. Variables are injected by `LLMClient.load_prompt`.

There are no DB-backed prompts in v1. Per-tenant overrides are out of scope.

---

## Loading

`LLMClient.load_prompt(name: str, config: ResolvedConfig, **extra) -> str`

1. Reads `src/zer0/prompts/<name>.md`.
2. Replaces all `{{ variable }}` occurrences with values derived from `ResolvedConfig` plus any `**extra` kwargs.
3. Returns the rendered string.

If a declared variable is not provided at render time, `load_prompt` raises `ValueError`. This prevents silent prompt truncation.

---

## Prompt contracts

Each prompt is a contract. Changing the variable list is a breaking change requiring a spec update in the same commit as the code change.

### `researcher`

**File:** `src/zer0/prompts/researcher.md`

**Purpose:** Extract structured enrichment data from a scraped web page.

**Variables:**

| Variable | Source |
|---|---|
| `company_name` | `RawLead.company_name` |
| `scraped_text` | Output of `scrape_page` |
| `offering_name` | `ResolvedConfig.offering_name` |
| `target_industries` | `ResolvedConfig.icp.target_industries` |
| `target_roles` | `ResolvedConfig.icp.target_roles` |

**Expected output:** JSON with fields: `company_description`, `industry`, `employee_count`, `technologies_used`, `pain_points`, `decision_makers`.

---

### `qualifier`

**File:** `src/zer0/prompts/qualifier.md`

**Purpose:** Score an enriched lead against the ICP rubric.

**Variables:**

| Variable | Source |
|---|---|
| `company_name` | `EnrichedLead.company_name` |
| `company_description` | `EnrichedLead.company_description` |
| `industry` | `EnrichedLead.industry` |
| `employee_count` | `EnrichedLead.employee_count` |
| `pain_points` | `EnrichedLead.pain_points` |
| `rubric_criteria` | `ResolvedConfig.qualification_config.rubric_criteria` (JSON) |
| `score_threshold` | `ResolvedConfig.qualification_config.score_threshold` |
| `min_employees` | `ResolvedConfig.icp.min_employees` |
| `max_employees` | `ResolvedConfig.icp.max_employees` |

**Expected output:** JSON with `criteria_scores` (list of `{criterion, score, reasoning}`) and `total_score` (0–100).

---

### `outreach`

**File:** `src/zer0/prompts/outreach.md`

**Purpose:** Draft a personalised first-touch outreach message.

**Variables:**

| Variable | Source |
|---|---|
| `company_name` | `QualifiedLead.company_name` |
| `company_description` | `QualifiedLead.company_description` |
| `pain_points` | `QualifiedLead.pain_points` |
| `offering_name` | `ResolvedConfig.offering_name` |
| `value_proposition` | `ResolvedConfig.value_proposition` |
| `tone` | `ResolvedConfig.outreach_config.tone` |
| `language` | Detected by `detect_language` tool |
| `channel` | `"email"` or `"whatsapp"` |

**Expected output (email):** JSON with `subject` and `body`.

**Expected output (WhatsApp):** JSON with `body` only. Length ≤ 1600 chars.

---

### `planner`

**File:** `src/zer0/prompts/planner.md`

**Purpose:** High-level campaign planning — which discover sources to prioritise, which leads to research first.

**Variables:**

| Variable | Source |
|---|---|
| `company_name` | `ResolvedConfig.company_name` (offering's parent tenant) |
| `offering_name` | `ResolvedConfig.offering_name` |
| `value_proposition` | `ResolvedConfig.value_proposition` |
| `target_industries` | `ResolvedConfig.icp.target_industries` |
| `target_roles` | `ResolvedConfig.icp.target_roles` |

**Expected output:** A brief prioritisation strategy (plain text). Not parsed — used only for structured logging/observability.

---

## Versioning

Prompts are files in git. History is visible via `git log src/zer0/prompts/`. Changing a prompt's **variable list** is a breaking change — update this spec file and the code in the same commit. Changing prompt **wording** alone does not require a spec change.

---

## Testing prompts

Use `approval_mode = true` on a campaign: the graph will draft messages and park at the approval gate. Review drafts via `GET /api/v1/leads/{id}/messages?status=pending_approval` before approving.

A `--dry-run` flag on `zer0 campaign run` is planned but out of scope for v1.
