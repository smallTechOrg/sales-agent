"""send_email tool.

Spec: spec/product/02-architecture.md — Tools table, Outreach channels
Spec: spec/product/03-db-schema.md — credentials column (encrypted, never in env)

Sends an email via the Gmail API using per-tenant OAuth credentials
(decrypted at runtime, never stored in plaintext).
"""

from __future__ import annotations

import base64
import email as email_lib
import json
import uuid
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from zer0.domain.outreach import OutreachDraft, SentMessage


def send_email(
    *,
    draft: OutreachDraft,
    encrypted_credentials: bytes,
    encryption_key: bytes,
) -> SentMessage:
    """Send the draft via Gmail API using per-tenant encrypted OAuth credentials.

    Args:
        draft: The approved outreach draft to send.
        encrypted_credentials: Fernet-encrypted JSON of the OAuth token dict.
        encryption_key: Fernet key used to decrypt credentials at runtime.
    """
    fernet = Fernet(encryption_key)
    creds_json = json.loads(fernet.decrypt(encrypted_credentials).decode())
    creds = Credentials(
        token=creds_json["token"],
        refresh_token=creds_json.get("refresh_token"),
        token_uri=creds_json.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_json["client_id"],
        client_secret=creds_json["client_secret"],
    )

    service = build("gmail", "v1", credentials=creds)

    msg = email_lib.message.EmailMessage()
    msg["Subject"] = draft.subject or "(no subject)"
    msg["From"] = "me"
    msg["To"] = draft.lead_id  # lead_id is the email address in this tool's contract
    msg.set_content(draft.body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()

    return SentMessage(
        **draft.model_dump(),
        message_id=str(uuid.uuid4()),
        sent_at=datetime.now(tz=timezone.utc),
        external_message_id=result.get("threadId", result["id"]),
    )
