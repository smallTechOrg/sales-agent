# Capability: Approval Gate (Person Selection)

**Status:** DRAFT

## Purpose

Gate outreach dispatch behind operator review. In non-auto modes, the operator reviews each qualified lead's people list and selects which people receive outreach. The graph parks until the operator acts.

## Trigger

`node_approval_gate` runs after `node_get_people`.

## Behavior

### `full_auto` and `approve_messages` modes

1. For all people in `AgentState.people`: set `approved_for_outreach = true`.
2. Set `approved_person_ids = [p.id for p in all_people]`.
3. Set `lead.stage = "outreach"` for all leads with people.
4. Proceed directly to `node_outreach`.

### `approve_qualify` and `approve_all` modes

1. For each lead with `stage == "people"`:
   a. Post `approval.pending` event.
   b. Send Slack notification: "Lead `{company_name}` has `{n}` people ready for review in campaign `{campaign_name}`."
   c. Set `lead.stage = "approval"`.
2. Return `{"pending_approval_person_ids": [...]}`.
3. The graph **parks** (returns to END). No outreach fires.

#### Resumption (operator approves)

1. Operator calls `POST /approvals/leads/{lead_id}/qualify?decision=approve` with a list of `approved_person_ids`.
2. API sets `person.approved_for_outreach = true` for selected people.
3. API sets `lead.stage = "outreach"`.
4. API re-invokes the graph with updated `approved_person_ids`.

#### Resumption (operator rejects lead)

1. Operator calls `POST /approvals/leads/{lead_id}/qualify?decision=reject&reason=...`.
2. API sets `lead.stage = "rejected"`, `lead.rejection_reason = reason`.
3. API inserts `approval.rejected` event.
4. No outreach fires for this lead.

## Inputs

| Key | Source |
|---|---|
| `leads` (stage == `people`) | `AgentState.leads` |
| `people` | `AgentState.people` |
| `approval_mode` | `ResolvedConfig.approval_mode` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.approved_person_ids` | `list[str]` — populated in auto modes |
| `AgentState.pending_approval_person_ids` | `list[str]` — populated in manual modes |
| `people` DB rows | `approved_for_outreach` updated |
| `leads` DB rows | `stage = "outreach"` or `"rejected"` |
| `events` DB rows | `approval.pending`, `approval.granted`, or `approval.rejected` |

## Failure modes

| Class | Response |
|---|---|
| No people to approve for a lead | Skip that lead, log `approval_no_people` |
| Operator timeout (no action for TTL) | Lead remains parked; re-notified on next campaign run |

## Out of scope

- Partial person approval for individual follow-up messages — that is handled by `approve_messages` mode.
- Bulk approve all leads across campaigns in one call (v2).
