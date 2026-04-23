# Capability: People Discovery

**Status:** DRAFT

## Purpose

Find individual decision-makers at qualified companies and store them as `Person` records, ready for the approval gate to select which people receive outreach.

## Trigger

`node_get_people` runs after `node_qualify`. It processes all leads with `stage == "qualification"`.

## Behavior

1. For each qualified lead:
   a. Call `find_all_people(lead, config.icp.target_roles)` to find decision-makers at the company.
   b. For each returned person:
      - Create a `PersonRow` with `lead_id`, `company_id`, `first_name`, `last_name`, `email`, `role`, `seniority_level`, `decision_maker_score`.
      - Set `approved_for_outreach = false` (default; approval gate sets this to true).
      - Deduplicate by `(lead_id, email)` — if a person with the same email already exists for this lead, skip.
   c. Set `lead.stage = "people"`.
   d. Persist `PersonRow` and updated `LeadRow`.
   e. Emit `lead.people_found` event with count.
2. If **no people** are found for a lead: log `no_people_found`, leave lead at `stage = "qualification"` (will fall through to approval gate with zero people — operator can block or manually add people in future).

## Inputs

| Key | Source |
|---|---|
| `leads` (stage == `qualification`) | `AgentState.leads` |
| `target_roles` | `ResolvedConfig.icp.target_roles` |
| `campaign_id`, `tenant_id` | `AgentState` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.people` | `list[Person]` |
| `AgentState.leads` | `stage` updated to `"people"` |
| `people` DB rows | `approved_for_outreach = false` |
| `leads` DB rows | `stage = "people"` |
| `events` DB rows | `lead.people_found` with count |

## Failure modes

| Class | Response |
|---|---|
| `find_all_people` tool error | Log `person_discovery_error`, skip lead, log event |
| No people found for lead | Log `no_people_found`, emit event, lead stays at `qualification` |
| Duplicate email within lead | Skip duplicate, log `person_duplicate_skipped` |

## Out of scope

- Email verification / deliverability checks.
- LinkedIn DM availability checks (v1 discovery sources only).
- Manual person entry via UI (v2).
