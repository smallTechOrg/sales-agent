"""draft_outreach tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  QualifiedLead + ResolvedConfig
Output: OutreachDraft (or list[OutreachDraft] for multi-channel)
"""

from __future__ import annotations

from zer0.domain import Contact, Lead
from zer0.domain.config import Channel, ResolvedConfig
from zer0.domain.outreach import OutreachDraft
from zer0.llm.client import LLMClient


def draft_outreach(
    *,
    lead: Lead,
    contact: Contact | None = None,
    channel: Channel,
    sequence_number: int = 1,
    llm: LLMClient,
    config: ResolvedConfig,
) -> OutreachDraft:
    """Generate a personalised outreach message for the given channel.

    sequence_number=1 is the first touch; higher values are follow-ups.
    """
    system = llm.load_prompt("outreach", config)
    user = (
        f"Channel: {channel.value}\n"
        f"Sequence: {sequence_number}\n"
        f"Contact name: {contact.full_name if contact else 'unknown'}\n"
        f"Contact role: {contact.role if contact else 'unknown'}\n"
        f"Company: {lead.company_name}\n"
        f"Research summary: {lead.research_summary}\n"
        f"Score rationale: {lead.rationale}\n"
        f"Signals: {', '.join(lead.signals)}\n"
        f"Language: {lead.detected_language or 'en'}\n\n"
        "Return the message body only (no JSON). "
        "For email also prepend 'Subject: <subject line>' on the first line."
    )

    body = llm.complete(system=system, user=user).strip()

    subject: str | None = None
    if channel == Channel.email and body.lower().startswith("subject:"):
        lines = body.splitlines()
        subject = lines[0].split(":", 1)[1].strip()
        body = "\n".join(lines[1:]).strip()

    return OutreachDraft(
        lead_id=lead.id,
        campaign_id=lead.campaign_id,
        tenant_id=lead.tenant_id,
        channel=channel,
        subject=subject,
        body=body,
        personalisation_notes=lead.rationale,
        config_snapshot=config,
        sequence_number=sequence_number,
    )
