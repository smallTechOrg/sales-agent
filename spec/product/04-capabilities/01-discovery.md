# Capability: Lead Discovery

**Status:** DRAFT

## Purpose

Discover raw leads that match the ideal customer profile (ICP) for a campaign, using one or more enabled discovery sources.

## Trigger

The agent graph enters `node_discover` after `node_resolve_config` succeeds.

## Behavior

1. Read `ResolvedConfig.discovery_config.sources` for the current campaign.
2. For each enabled source, invoke the corresponding tool(s):
   - `linkedin_search` — LinkedIn Sales Navigator keyword search.
   - `web` source — runs **all available web adapters** and aggregates results:
     - `duckduckgo_search` — always runs (no API key required).
     - `web_search` (Tavily) — runs if `ZER0_TAVILY_API_KEY` is configured.
   - `directory_search` — Apollo/Crunchbase-style directory lookup.
3. Deduplicate results by `(company_name, website)` across sources.
4. Write one `LeadRow` per unique raw lead with `stage = "discovered"`.
5. Emit `lead_discovered` event for each lead written.
6. Return the list of raw leads to `AgentState.raw_leads`.

## Inputs

| Key | Source |
|---|---|
| `icp` | `ResolvedConfig.icp` |
| `discovery_config.sources` | `ResolvedConfig.discovery_config` |
| `tavily_api_key` | `Settings.tavily_api_key` (optional — enables Tavily adapter) |
| `campaign_id`, `tenant_id` | `AgentState` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.raw_leads` | `list[RawLead]` |
| `leads` DB rows | `stage = "discovered"` |
| `events` DB rows | `event_type = "lead_discovered"` |

## Failure modes

| Class | Response |
|---|---|
| Source API 429 / quota exceeded | Log `discovery_rate_limited`, skip that source, continue with others |
| Source API auth error | Log `discovery_auth_failed`, skip source |
| Zero leads found | Set `AgentState.error` with `"no_leads_found"`, transition to error handler |
| Tool raises unhandled exception | Log `discovery_tool_error`, skip source, continue |

## Out of scope

- Enrichment — raw leads are company names and URLs only; enrichment is a separate capability.
- Scoring — no ICP scoring happens at discovery time.
- Pagination across multiple pages of results — v1 returns the first page only.
