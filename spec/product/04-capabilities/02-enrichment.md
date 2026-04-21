# Capability: Lead Enrichment

**Status:** DRAFT

## Purpose

Research a raw lead by scraping its website and using an LLM to extract structured enrichment data.

## Trigger

For each `RawLead` in `AgentState.raw_leads`, the agent calls `node_research` which invokes `enrich_lead`.

## Behavior

1. For each raw lead:
   a. Scrape the lead's `website` with `scrape_page`.
   b. Look up contact details via `find_contact` (stub — best-effort).
   c. Call `enrich_lead` (LLM) with raw lead + scraped text to extract:
      - `company_description`
      - `industry`
      - `employee_count`
      - `technologies_used`
      - `pain_points`
      - `decision_makers`
   d. Write enriched fields back to `LeadRow`; stage → `"researched"`.
   e. Emit `lead_researched` event.
2. Return list of `EnrichedLead` in `AgentState.enriched_leads`.

## Inputs

| Key | Source |
|---|---|
| `raw_leads` | `AgentState.raw_leads` |
| `researcher.md` prompt | `src/zer0/prompts/researcher.md` |
| LLM settings | `ResolvedConfig` → `Settings` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.enriched_leads` | `list[EnrichedLead]` |
| `leads` DB rows | `stage = "researched"` |
| `events` DB rows | `event_type = "lead_researched"` |

## Failure modes

| Class | Response |
|---|---|
| Scrape returns empty body | Proceed with empty body; LLM may produce partial enrichment |
| LLM returns unparseable response | Log `enrichment_parse_error`, set partial fields, continue |
| `find_contact` not implemented | Stub logs `NotImplementedError`, contact fields remain null |
| httpx timeout | Log `scrape_timeout`, use empty body |

## Out of scope

- Sending emails to extracted contacts — that is outreach, a separate capability.
- Verifying contact email deliverability.
