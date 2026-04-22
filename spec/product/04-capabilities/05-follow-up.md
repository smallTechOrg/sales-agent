# Capability: Follow-Up

**Status:** DRAFT

## Purpose

Send cadenced follow-up messages to contacts who have not responded, up to the configured maximum number of follow-ups.

## Trigger

The `node_check_replies` loop runs after `node_outreach`. It loops until all follow-up steps are exhausted for all active contacts, or a positive reply stops outreach for a lead.

## Behavior

1. Read `ResolvedConfig.outreach_config.follow_up_days` — a list of day-offsets, e.g. `[3, 7, 14]`.
2. For each step:
   a. Poll for replies via `check_replies`.
   b. If a **positive reply** is found for any contact on a lead:
      - Reply handling takes over (see capability 06).
      - Exit the follow-up loop for that lead.
   c. Otherwise, on the scheduled offset day, draft and send a follow-up to each active contact (i.e. `approved_for_outreach=true` and `outreach_stopped=false`).
   d. Write `MessageRow(status="sent", sequence=n, contact_id=...)`.
   e. Emit `followup_sent` event.
3. After all steps complete with no positive reply, set lead `stage = "no_contact"`.

## Inputs

| Key | Source |
|---|---|
| `sent_messages` | `AgentState.sent_messages` |
| `contacts` | `AgentState.contacts` |
| `follow_up_days` | `ResolvedConfig.outreach_config.follow_up_days` |
| `max_follow_ups` | `ResolvedConfig.outreach_config.max_follow_ups` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.sent_messages` | Appended with follow-up messages |
| `messages` DB rows | `status = "sent"`, `sequence > 0`, `contact_id` set |
| `events` DB rows | `followup_sent` per step |

## Failure modes

| Class | Response |
|---|---|
| Send fails on follow-up | Log error, continue to next step; do not skip remaining steps |
| Max follow-ups reached | Emit `followup_exhausted`, set `lead.stage = "no_contact"`, exit loop |

## Out of scope

- Branching follow-up sequences based on reply sentiment (v1 is linear).
- Per-contact day-offset customisation.
