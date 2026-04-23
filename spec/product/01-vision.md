# Vision

Status: DRAFT

## What Zer0 is

Zer0 is a **multi-tenant autonomous sales agent platform** that runs the entire top-of-funnel pipeline — from cold prospecting to first positive reply — without human intervention.

A tenant defines everything about how the agent behaves via a web dashboard. Zer0 then executes: it searches for leads, researches them, scores them, and sends personalised outreach. Every action is logged, every decision is inspectable, and every event is posted to Slack.

**Primary user (v1):** JP+smallTech's own sales team.  
**Secondary user (v1+):** JP+smallTech's clients, onboarded as tenants on a managed service basis.  
**End state:** A self-serve SaaS platform any B2B business can operate independently.

---

## Core principle: everything is configuration

**Nothing in Zer0 is hardcoded.** Every behavioural parameter — what to search, how to research, how to score, what to say, how often to follow up, who to notify, when to hand off — is a configuration value owned by the tenant. Configuration lives in the database and is editable live via the dashboard. Changes take effect on the next agent tick. No code change. No redeploy. No restart.

This applies at three levels:

```
Tenant
 └── Offering          ← what you sell; sets defaults for all campaigns under it
      └── Campaign      ← a running instance; can override any Offering field
```

A value set at Campaign level overrides the Offering default. A value set at Offering level is the default for all campaigns under it. Nothing falls back to a hardcoded system value — if a field is unset, the agent surfaces a validation error, not a silent default.

---

## The pipeline

```
DISCOVER → SCRAPE → IDENTIFY LEADS → RESEARCH → QUALIFY → PEOPLE → APPROVAL → OUTREACH
```

Every stage is independently configurable per campaign. A **Link** is a raw URL produced by discovery; a **Lead** is a company entity extracted from a link and progressed through the pipeline; a **Person** is an individual at that company.

| Stage              | What happens | What is configurable |
| ------------------ | ------------ | -------------------- |
| **Discover**       | Agent searches for URLs matching the ICP across enabled sources. | Sources (LinkedIn, web search, directories), search queries, geography, volume target per run. |
| **Scrape**         | Agent fetches and cleans the full page text for each discovered link. | Scraping timeout, content selectors. |
| **Identify Leads** | LLM extracts company entities from each page, creating one Lead per identified company. | Extraction prompt, company filters, deduplication rules. |
| **Research**       | Agent enriches each lead with company context, buying signals, and public data. Cumulative — signals are appended across runs. | Depth of research, which signals to look for, which data sources to use. |
| **Qualify**        | Agent scores each lead against the ICP rubric. Below-threshold leads are rejected with a reason. | Rubric criteria and weights, score threshold, what counts as a disqualifying signal. |
| **People**         | Agent finds individual decision-makers at qualified companies. | Target roles, seniority levels, max people per lead. |
| **Approval**       | Operator reviews qualified leads and selects which people to reach out to. | Approval mode (auto / qualify gate / message gate / full gate). |
| **Outreach**       | Agent drafts and sends personalised messages per person, then follows up until a positive reply is received. Positive reply from one person stops all other people for that lead. | Channels, tone, language, message templates, follow-up count, follow-up spacing, send schedule. |

---

## What is configurable — complete list

### Tenant level
- Name, branding.
- API credentials: Google Workspace OAuth, WhatsApp Business API, Slack webhook.
- Notification rules: which events trigger Slack alerts and to which channel.
- Default approval mode for new campaigns (auto-approve qualify step vs. human review).
- Re-targeting policy: cooldown period before a rejected lead can be re-qualified.

### Offering level (inheritable by campaigns)
- Name, description, value proposition, key pain points.
- ICP: target industries, target company sizes, target geographies, target roles, keywords, negative keywords.
- Qualification rubric: scoring criteria, criterion weights, minimum score threshold.
- Outreach settings: channels enabled, default tone, default language, message templates (first touch + each follow-up), follow-up count, follow-up spacing.
- Discovery settings: preferred sources, search query templates, volume per run.

### Campaign level (overrides Offering defaults)
- Every Offering-level field above can be overridden per campaign.
- Additionally: run schedule (cron), active/paused status, total lead cap, approval mode override.

### Per-lead (operator-initiated)
- Manual stage override (move a lead forward or backward in the pipeline).
- Block a lead permanently (never contact again).
- Trigger an immediate follow-up outside the normal sequence.
- Edit an outreach draft before it is sent (if approval mode is enabled).

---

## Approval modes

Configurable per campaign:

| Mode | Behaviour |
| ---- | --------- |
| `full_auto` | Agent discovers, qualifies, and sends without any human step. |
| `approve_qualify` | Human reviews the qualified shortlist before outreach fires. |
| `approve_messages` | Human sees each drafted message and approves before it is sent. |
| `approve_all` | Human approves both the qualified shortlist and each message. |

---

## Channels

Configurable per offering/campaign. Enabled channels in v1:

| Channel  | Notes |
| -------- | ----- |
| Email    | Via tenant's Google Workspace account (OAuth). |
| WhatsApp | Via WhatsApp Business API. |
| LinkedIn | Discovery source only in v1. DM outreach is v2. |

---

## Handoff

Zer0 owns the conversation until a positive reply is received. On positive reply:
- Lead is flagged **Responded** in the database.
- Slack notification is sent to the tenant's configured channel.
- No further automated messages are sent.
- Human takes over.

The definition of "positive reply" (keyword matching, sentiment threshold) is configurable per campaign.

---

## Data stored per lead

- Full research trail: every source consulted, every signal found.
- Qualification score and full rationale (per criterion).
- Every message sent: channel, full text, timestamp, sequence position.
- Every reply received: channel, content, timestamp, detected sentiment.
- Full audit log of every agent action and every configuration value active at the time.

---

## Re-targeting

Configurable per tenant/offering/campaign:
- Cooldown period before a rejected lead re-enters qualification (default: 90 days).
- Whether previously contacted leads can ever be re-contacted (default: no).
- Whether a new qualifying signal bypasses the cooldown (configurable).

---

## Monetisation path

| Phase | Model |
| ----- | ----- |
| Now | Internal — Zer0 runs campaigns for JP+smallTech. |
| Near-term | Managed service — JP+smallTech operates Zer0 for clients as tenants. |
| Later | Self-serve SaaS — tenants onboard and operate independently. |

---

## Success criteria

- A tenant can configure a complete offering and launch a campaign in under 30 minutes with no engineering involvement.
- Any configuration field can be changed on a live campaign and takes effect within one agent tick, with no restart.
- The agent discovers and qualifies 10–50 leads per day per campaign.
- Qualification precision ≥ 80%: at least 8 in 10 qualified leads are considered genuinely relevant by a human reviewer.
- Outreach messages are personalised, pass a human quality bar, and are not detectable as boilerplate.
- Every agent action is visible in the dashboard and posted to Slack within 60 seconds.
- The full audit log for any lead shows every decision made and every config value that drove it.

---

## Out of scope (v1)

- LinkedIn DM outreach (LinkedIn is discovery only).
- Inbound lead handling.
- CRM sync or pipeline management.
- A/B testing framework.
- Self-serve tenant sign-up (manual onboarding by JP+smallTech in v1).
- TRAI/DPDP compliance infrastructure (v2).
