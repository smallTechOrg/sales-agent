"""check_replies tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  campaign_id, tenant credentials
Output: list[Reply]

Polls Gmail and/or WhatsApp for inbound replies and returns them for
the OUTREACH → RESPOND edge to process.
"""

from __future__ import annotations

import json
import base64
from datetime import datetime, timezone

from cryptography.fernet import Fernet

from zer0.domain.config import Channel
from zer0.domain.outreach import Reply, Sentiment


def check_replies(
    *,
    campaign_id: str,
    tenant_id: str,
    channels: list[Channel],
    encrypted_credentials: bytes,
    encryption_key: bytes,
    since_timestamp_ms: int | None = None,
) -> list[Reply]:
    """Poll configured channels for new inbound replies.

    Args:
        campaign_id: Used to filter / label-match threads.
        tenant_id:   Tenant owning these credentials.
        channels:    Which channels to poll (email / whatsapp).
        encrypted_credentials: Fernet-encrypted JSON with per-channel creds.
        encryption_key: Fernet key to decrypt credentials at runtime.
        since_timestamp_ms: Only return messages newer than this epoch-ms.

    Returns:
        List of Reply objects (sentiment not yet set — classifier runs later).
    """
    fernet = Fernet(encryption_key)
    creds = json.loads(fernet.decrypt(encrypted_credentials).decode())

    replies: list[Reply] = []

    if Channel.email in channels:
        replies.extend(
            _poll_gmail(
                campaign_id=campaign_id,
                tenant_id=tenant_id,
                creds=creds,
                since_timestamp_ms=since_timestamp_ms,
            )
        )

    if Channel.whatsapp in channels:
        replies.extend(
            _poll_whatsapp(
                campaign_id=campaign_id,
                tenant_id=tenant_id,
                creds=creds,
                since_timestamp_ms=since_timestamp_ms,
            )
        )

    return replies


def _poll_gmail(
    *,
    campaign_id: str,
    tenant_id: str,
    creds: dict,
    since_timestamp_ms: int | None,
) -> list[Reply]:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    gmail_creds = creds.get("gmail", {})
    if not gmail_creds:
        return []

    oauth = Credentials(
        token=gmail_creds["token"],
        refresh_token=gmail_creds.get("refresh_token"),
        token_uri=gmail_creds.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=gmail_creds["client_id"],
        client_secret=gmail_creds["client_secret"],
    )

    service = build("gmail", "v1", credentials=oauth)

    query = "in:inbox label:zer0-campaign"
    if since_timestamp_ms:
        after_sec = since_timestamp_ms // 1000
        query += f" after:{after_sec}"

    result = service.users().messages().list(userId="me", q=query, maxResults=100).execute()
    messages = result.get("messages", [])

    replies: list[Reply] = []
    for msg_ref in messages:
        full = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
        body = _extract_gmail_body(full)
        ts_ms: int = int(full.get("internalDate", 0))
        replies.append(
            Reply(
                lead_id="",  # resolved downstream by matching thread
                tenant_id=tenant_id,
                message_id=None,
                channel=Channel.email,
                content=body,
                received_at=datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                sentiment=None,
            )
        )
    return replies


def _extract_gmail_body(message: dict) -> str:
    payload = message.get("payload", {})
    parts = payload.get("parts", [])
    if not parts:
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace") if data else ""
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace") if data else ""
    return ""


def _poll_whatsapp(
    *,
    campaign_id: str,
    tenant_id: str,
    creds: dict,
    since_timestamp_ms: int | None,
) -> list[Reply]:
    # WhatsApp inbound messages are delivered via webhook (registered separately).
    # This stub exists as a placeholder; real polling is handled by the webhook endpoint
    # in src/zer0/api/messages.py which writes Reply rows to the DB.
    # The graph reads those rows rather than polling the API directly.
    return []
