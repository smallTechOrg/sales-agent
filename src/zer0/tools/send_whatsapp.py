"""send_whatsapp tool.

Spec: spec/product/02-architecture.md — Tools table, Outreach channels
Spec: spec/product/03-db-schema.md — credentials column (encrypted)

Sends a WhatsApp message via the Meta Cloud API (WhatsApp Business Platform).
Per-tenant credentials (phone_number_id + access_token) are decrypted at runtime.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import httpx
from cryptography.fernet import Fernet

from zer0.domain.outreach import OutreachDraft, SentMessage

_META_API_VERSION = "v19.0"
_SEND_URL_TEMPLATE = "https://graph.facebook.com/{version}/{phone_number_id}/messages"


def send_whatsapp(
    *,
    draft: OutreachDraft,
    recipient_phone: str,
    encrypted_credentials: bytes,
    encryption_key: bytes,
) -> SentMessage:
    """Send message via Meta WhatsApp Cloud API using per-tenant encrypted credentials.

    Args:
        draft: The approved outreach draft.
        recipient_phone: E.164 formatted phone number of the recipient.
        encrypted_credentials: Fernet-encrypted JSON with keys:
            phone_number_id, access_token
        encryption_key: Fernet key to decrypt credentials at runtime.
    """
    fernet = Fernet(encryption_key)
    creds = json.loads(fernet.decrypt(encrypted_credentials).decode())

    phone_number_id: str = creds["phone_number_id"]
    access_token: str = creds["access_token"]

    url = _SEND_URL_TEMPLATE.format(
        version=_META_API_VERSION,
        phone_number_id=phone_number_id,
    )
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": draft.body},
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    wa_id: str = data["messages"][0]["id"]

    return SentMessage(
        **draft.model_dump(),
        message_id=str(uuid.uuid4()),
        sent_at=datetime.now(tz=timezone.utc),
        external_message_id=wa_id,
    )
