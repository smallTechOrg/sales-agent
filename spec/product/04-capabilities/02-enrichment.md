# Capability: Link Scraping, Lead Identification, and Research

**Status:** DRAFT

## Purpose

Convert raw discovery URLs into structured company entities (`Lead`s), then enrich each lead with research data. Three sequential sub-steps: scrape link content, extract companies via LLM, and research each company cumulatively.

## Sub-step 1: Scrape links (`node_scrape_links`)

### Trigger
Runs after `node_discover`. Processes all `Link` objects in `AgentState.links` where `page_text is None`.

### Behavior
1. For each unscraped link: call `scrape_page(link.url)` to fetch and clean page HTML.
2. Store cleaned text in `link.page_text`; set `link.scraped_at = now()`.
3. Persist updated `LinkRow`.
4. Scraping errors are non-fatal — a link with empty text still proceeds to identification (LLM may produce no leads).

---

## Sub-step 2: Identify leads (`node_identify_leads`)

### Trigger
Runs after `node_scrape_links`. Processes all `Link` objects where `page_text is not None`.

### Behavior
1. For each link: call `identify_leads(link, config.icp)` — an LLM call that reads the page text and extracts company entities.
2. For each extracted company: create one `Lead` (stage `prospect`) with `company_name`, `domain`, `industry`, `business_type` populated.
3. Deduplicate by `(tenant_id, campaign_id, domain)` — if the same domain already exists as a lead in this campaign, skip creation.
4. Set `lead.link_id` to the source link.
5. Persist `LeadRow` (stage `prospect`).
6. Emit `lead_identified` event per created lead.
7. Return `AgentState.leads`.

**Key rule:** One link page can produce **zero or more** leads (e.g. a directory page lists 10 companies → 10 leads).

---

## Sub-step 3: Research (`node_research`)

### Trigger
Runs after `node_identify_leads` for all leads with `stage == "prospect"`.

### Behavior

Research is **independent web research about the company** — it does not re-use the discovery page text. The three micro-steps are:

**3A — Web search for the company:**
1. Construct a research query: `"{company_name} {domain} company overview"`.
2. Call `web_search` (Tavily if configured, else `duckduckgo_search`) with the query. Collect up to 5 result URLs.
3. For each result URL: call `scrape_page(url)` to fetch page content. Errors are non-fatal — skip failed pages, continue with the rest.

**3B — Synthesis via LLM:**
4. Call `enrich_lead(lead, research_sources, config.icp)` where `research_sources` is the list of freshly scraped page texts.
5. The LLM reads the research sources and produces `company_summary` (str) and `recent_signals` (list[str]).

**3C — Cumulative write:**
6. **Append** new summary to `lead.research_summary` (separator `\n\n---\n`). Never overwrite.
7. **Append** new signals to `lead.signals` (deduplicated). Never overwrite.
8. **Append** same data to the tenant-wide `CompanyRow.research_summary` and `CompanyRow.signals`.
9. Set `lead.last_researched_at = now()`; set `lead.stage = "research"`.
10. Persist updated `LeadRow` and `CompanyRow`.
11. Emit `lead.researched` event.

## Inputs

| Key | Source |
|---|---|
| `links` | `AgentState.links` |
| `leads` | `AgentState.leads` |
| `icp` | `ResolvedConfig.icp` |
| `researcher.md` prompt | `src/zer0/prompts/researcher.md` |
| `identifier.md` prompt | `src/zer0/prompts/identifier.md` |
| `web_search` / `duckduckgo_search` tool | Used in Sub-step 3A to fetch fresh company pages |
| `scrape_page` tool | Used in Sub-step 3A to extract page text from research URLs |
| `tavily_api_key` | `Settings.tavily_api_key` (optional — enables Tavily for research queries) |
| LLM settings | `ResolvedConfig` → `Settings` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.links` | Updated with `page_text` populated |
| `AgentState.leads` | `list[Lead]` — stage `prospect` or `research` |
| `links` DB rows | `page_text`, `scraped_at` populated |
| `leads` DB rows | `stage = "prospect"` (after identify) or `"research"` (after enrich) |
| `events` DB rows | `lead_identified` and `lead_researched` |

## Failure modes

| Class | Response |
|---|---|
| Scrape returns empty body | Log `scrape_empty`, link.page_text = "", proceed to identification |
| Scrape timeout | Log `scrape_timeout`, skip link, continue |
| Identification returns no companies | Log `identification_no_leads`, skip link, continue |
| LLM returns unparseable identify response | Log `identification_parse_error`, skip link |
| LLM returns unparseable research response | Log `enrichment_parse_error`, set partial fields, continue |

## Out of scope

- Verifying person email deliverability.
- Sending emails to any extracted people — outreach is a separate capability.
