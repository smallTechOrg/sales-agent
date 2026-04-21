# Capability: Reply Handling

**Status:** DRAFT

## Purpose

Detect inbound replies from leads, classify their sentiment, and update lead stage accordingly.

## Trigger

`check_replies` is called at the start of each follow-up loop iteration and as a scheduled background sweep.

## Behavior

1. For each `SentMessage` with channel `email`, poll Gmail for replies using the thread ID.
2. For each reply found:
   a. Classify sentiment via LLM (`positive`, `neutral`, `negative`, `unsubscribe`).
   b. Write `ReplyRow` with sentiment and raw body.
   c. Update `LeadRow.stage`:
      - `"responded"` for `positive` or `neutral`.
      - `"opted_out"` for `unsubscribe`.
      - `"responded"` for `negative` (operator still sees it).
   d. Emit `reply_received` event with sentiment.
3. For WhatsApp: stub — webhook-based reply handling is out of scope for v1. Returns empty list.

## Inputs

| Key | Source |
|---|---|
| `sent_messages` | `AgentState.sent_messages` |
| `google_oauth_token_enc` | `ResolvedConfig` (decrypted) |

## Outputs

| Output | Type |
|---|---|
| `AgentState.replies` | `list[Reply]` |
| `replies` DB rows | With `sentiment` set |
| `leads` DB rows | `stage` updated |
| `events` DB rows | `reply_received` per reply |

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
