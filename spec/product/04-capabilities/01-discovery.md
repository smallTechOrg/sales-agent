# Capability: Link Discovery

**Status:** DRAFT

## Purpose

Discover raw URLs that match the ideal customer profile (ICP) for a campaign, using one or more enabled discovery sources. Each URL is stored as a `Link` for downstream scraping and lead extraction.

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
3. Deduplicate results by URL against existing `links` rows **for this tenant** (`(tenant_id, url)` unique). A URL already seen in any prior campaign for this tenant is not re-inserted.
4. Trim to `min(len(results), ResolvedConfig.discovery_config.volume_per_run)`.
5. For each unique new URL: write one `LinkRow` (unique per `(tenant_id, url)`). Set `source`, `campaign_id` (first discoverer). Write a `link_leads` row associating the link with the current campaign.
6. For a URL already existing (same tenant, different campaign): skip `LinkRow` insert; still write a `link_leads` row for the current campaign so the link participates in this run.
7. Emit `link.discovered` event for each newly inserted `LinkRow`.
8. Return the list of `Link` objects to `AgentState.links`.

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
| `AgentState.links` | `list[Link]` |
| `links` DB rows | Upserted on `(tenant_id, url)`. `page_text = NULL`, `scraped_at = NULL` for new rows; re-used as-is for existing rows. |
| `link_leads` DB rows | One row per `(link_id, campaign_id)` association. |
| `events` DB rows | `event_type = "link.discovered"` — only for newly inserted `LinkRow`s |

## Failure modes

| Class | Response |
|---|---|
| Source API 429 / quota exceeded | Log `discovery_rate_limited`, skip that source, continue with others |
| Source API auth error | Log `discovery_auth_failed`, skip source |
| Zero links found | Set `AgentState.error` with `"no_leads_found"`, transition to error handler |
| Tool raises unhandled exception | Log `discovery_tool_error`, skip source, continue |

## Out of scope

- Scraping page content — that is the `scrape_links` node (next step).
- Extracting company entities from pages — that is the `identify_leads` node.
- Scoring — no ICP scoring happens at discovery time.
- Pagination across multiple pages of results — v1 returns the first page only.
