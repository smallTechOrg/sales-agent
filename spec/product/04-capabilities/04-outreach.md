# Capability: Outreach

**Status:** DRAFT

## Purpose

Draft personalised first-touch messages for each approved contact and send them via the configured channels (email and/or WhatsApp).

## Trigger

`node_outreach` runs after `node_approval_gate`. For each contact with `approved_for_outreach = true` in `AgentState.contacts`.

## Behavior

1. For each approved `Contact`:
   a. Load the parent `Lead` from `AgentState.leads`.
   b. Detect message language via `detect_language(lead)` (LLM, falls back to `"en"`).
   c. For each enabled channel (`email`, `whatsapp`) in `ResolvedConfig.outreach_config`:
      - Render `outreach.md` prompt with lead data, contact details, and channel-specific constraints.
      - Call `draft_outreach(lead, contact, config.outreach_config)` (LLM) to produce subject + body.
      - Send via `send_email` or `send_whatsapp`.
      - Write `MessageRow` with `contact_id`, `status = "sent"`.
      - Emit `message_sent` event.
2. If approval mode is `approve_messages` or `approve_all`, drafts go to `status = "pending_approval"` first and the graph parks until approved via the API.

```mermaid
sequenceDiagram
    participant G as Graph (node_outreach)
    participant LLM
    participant Gmail
    participant WA as WhatsApp
    participant DB

    G->>LLM: detect language
    LLM-->>G: "en"
    G->>LLM: draft_outreach(lead, contact, email)
    LLM-->>G: subject + body
    G->>Gmail: send_email()
    Gmail-->>G: message_id
    G->>DB: MessageRow(contact_id=..., status="sent")
    G->>LLM: draft_outreach(lead, contact, whatsapp)
    LLM-->>G: body
    G->>WA: send_whatsapp()
    WA-->>G: waid
    G->>DB: MessageRow(contact_id=..., status="sent")
```

## Inputs

| Key | Source |
|---|---|
| `contacts` (approved_for_outreach=true) | `AgentState.contacts` |
| `leads` | `AgentState.leads` |
| `channels` | `ResolvedConfig.outreach_config.channels` |
| `google_oauth_token_enc` | `ResolvedConfig` (decrypted) |
| `whatsapp_api_key_enc` | `ResolvedConfig` (decrypted) |
| `outreach.md` prompt | `src/zer0/prompts/outreach.md` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.sent_messages` | `list[SentMessage]` |
| `messages` DB rows | `status = "sent"` or `"failed"`, with `contact_id` set |
| `events` DB rows | `message_sent` or `message_send_failed` |

## Failure modes

| Class | Response |
|---|---|
| Gmail API error | Log `email_send_failed`, write `MessageRow(status="failed")`, continue to next contact |
| WhatsApp API 4xx | Log `whatsapp_send_failed`, write `MessageRow(status="failed")`, continue |
| Approval mode — no approval within TTL | Park state; operator must approve or reject via API |
| LLM draft parse error | Log `draft_parse_error`, skip channel for this contact |

## Out of scope

- A/B testing of message variants.
- Unsubscribe handling in v1.
