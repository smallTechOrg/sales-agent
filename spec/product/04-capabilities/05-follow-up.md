# Capability: Follow-Up

**Status:** DRAFT

## Purpose

Send cadenced follow-up messages to leads who have not responded, up to the configured maximum number of follow-ups.

## Trigger

`node_follow_up_loop` runs after `node_outreach`. It loops until all follow-up steps are exhausted or a reply is detected.

## Behavior

1. Read `ResolvedConfig.outreach_config.follow_up_days` — a list of day-offsets, e.g. `[3, 7, 14]`.
2. For each step:
   a. Poll for replies via `check_replies`.
   b. If a reply is found for any lead, exit the loop for that lead (reply handling takes over).
   c. Otherwise, on the scheduled offset day, draft and send a follow-up via the same channels as the initial outreach.
   d. Write `MessageRow(status="sent", sequence=n)`.
   e. Emit `followup_sent` event.
3. After all steps complete with no reply, set lead `stage = "exhausted"`.

## Inputs

| Key | Source |
|---|---|
| `sent_messages` | `AgentState.sent_messages` |
| `follow_up_days` | `ResolvedConfig.outreach_config.follow_up_days` |
| `max_follow_ups` | `ResolvedConfig.outreach_config.max_follow_ups` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.sent_messages` | Appended with follow-up messages |
| `messages` DB rows | `status = "sent"`, `sequence > 0` |
| `events` DB rows | `followup_sent` per step |

## Failure modes

| Class | Response |
|---|---|
| Send fails on follow-up | Log error, continue to next step; do not skip remaining steps |
| Max follow-ups reached | Emit `followup_exhausted`, transition out of loop |

## Out of scope

- Branching follow-up sequences based on reply sentiment (v1 is linear).
- Per-lead day-offset customisation.
