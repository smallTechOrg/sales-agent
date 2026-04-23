# Capability: Reply Handling

**Status:** DRAFT

## Purpose

Detect inbound replies from people, classify their sentiment, update lead stage accordingly, and stop outreach to all other people at the same company when a positive reply is received.

## Trigger

`check_replies` is called inside `node_check_replies` on each loop iteration.

## Behavior

1. For each `SentMessage` with channel `email`, poll Gmail for replies using the thread ID.
2. For each reply found:
   a. Identify the `Person` from the message's `person_id`.
   b. Classify sentiment via LLM (`positive`, `neutral`, `negative`, `unsubscribe`).
   c. Write `ReplyRow` with `person_id`, sentiment, and raw body.
   d. Emit `reply_received` event with sentiment.
3. If sentiment is `positive`:
   a. Set `lead.stage = "first_contact"`.
   b. Set `person.outreach_stopped = true` on **all other** `Person` rows for the same `lead_id` (sibling people). This prevents further follow-ups to those people.
   c. Emit `first_contact.triggered` event.
   d. Post Slack alert to the tenant's configured channel.
4. If sentiment is `unsubscribe`:
   a. Set `person.outreach_stopped = true` on this person only.
   b. Emit `reply_received` event with `sentiment = "unsubscribe"`.
5. For `neutral` or `negative`: write `ReplyRow`, emit event. No stage change.
6. For WhatsApp: stub — webhook-based reply handling is out of scope for v1. Returns empty list.

## Inputs

| Key | Source |
|---|---|
| `sent_messages` | `AgentState.sent_messages` |
| `people` | `AgentState.people` |
| `google_oauth_token_enc` | `ResolvedConfig` (decrypted) |

## Outputs

| Output | Type |
|---|---|
| `AgentState.replies` | `list[Reply]` |
| `replies` DB rows | With `person_id` and `sentiment` set |
| `people` DB rows | `outreach_stopped = true` on sibling people on positive reply |
| `leads` DB rows | `stage = "first_contact"` on positive reply |
| `events` DB rows | `reply_received`, `first_contact.triggered` |

## Failure modes

| Class | Response |
|---|---|
| Gmail poll 401 (token expired) | Log `gmail_auth_expired`, yield empty; operator must re-auth |
| LLM sentiment parse error | Default to `"neutral"`, log warning |
| Thread ID not found | Log `reply_thread_not_found`, skip |

## Out of scope

- Automatic reply drafting (responding to a reply is a future capability).
- WhatsApp webhook integration in v1.
- SMS replies.
