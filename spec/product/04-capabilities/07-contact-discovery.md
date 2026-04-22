# Capability: Contact Discovery

**Status:** DRAFT

## Purpose

Find individual decision-makers at qualified companies and store them as `Contact` records, ready for the approval gate to select which contacts receive outreach.

## Trigger

`node_get_contacts` runs after `node_qualify`. It processes all leads with `stage == "qualification"`.

## Behavior

1. For each qualified lead:
   a. Call `find_all_contacts(lead, config.icp.target_roles)` to find decision-makers at the company.
   b. For each returned contact:
      - Create a `ContactRow` with `lead_id`, `first_name`, `last_name`, `email`, `role`, `seniority_level`, `decision_maker_score`.
      - Set `approved_for_outreach = false` (default; approval gate sets this to true).
      - Deduplicate by `(lead_id, email)` — if a contact with the same email already exists for this lead, skip.
   c. Set `lead.stage = "contacts"`.
   d. Persist `ContactRow` and updated `LeadRow`.
   e. Emit `contacts.found` event with count.
2. If **no contacts** are found for a lead: log `no_contacts_found`, leave lead at `stage = "qualification"` (will fall through to approval gate with zero contacts — operator can block or manually add contacts in future).

## Inputs

| Key | Source |
|---|---|
| `leads` (stage == `qualification`) | `AgentState.leads` |
| `target_roles` | `ResolvedConfig.icp.target_roles` |
| `campaign_id`, `tenant_id` | `AgentState` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.contacts` | `list[Contact]` |
| `AgentState.leads` | `stage` updated to `"contacts"` |
| `contacts` DB rows | `approved_for_outreach = false` |
| `leads` DB rows | `stage = "contacts"` |
| `events` DB rows | `contacts.found` with count |

## Failure modes

| Class | Response |
|---|---|
| `find_all_contacts` tool error | Log `contact_discovery_error`, skip lead, log event |
| No contacts found for lead | Log `no_contacts_found`, emit event, lead stays at `qualification` |
| Duplicate email within lead | Skip duplicate, log `contact_duplicate_skipped` |

## Out of scope

- Email verification / deliverability checks.
- LinkedIn DM availability checks (v1 discovery sources only).
- Manual contact entry via UI (v2).
