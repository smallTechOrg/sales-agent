# Phase-5 gate — ORM model tests
# Spec: spec/engineering/phases.md § Phase 5
# These tests exercise Python-level construction only — no DB connection required.
from __future__ import annotations

from zer0.db.models import (
    CampaignRow,
    EventRow,
    LeadRow,
    MessageRow,
    OfferingRow,
    ReplyRow,
    TenantRow,
)


class TestOrmModelInstantiation:
    def test_tenant_row_defaults(self) -> None:
        row = TenantRow(name="Acme Corp")
        assert row.name == "Acme Corp"
        assert row.deleted_at is None
        # SQLAlchemy column defaults are applied at DB flush, not on construction
        assert row.google_oauth_token_enc is None
        assert row.whatsapp_api_key_enc is None

    def test_campaign_row_defaults(self) -> None:
        row = CampaignRow(
            tenant_id="t1",
            offering_id="o1",
            name="Q3 Campaign",
        )
        assert row.name == "Q3 Campaign"
        assert row.approval_mode is None
        assert row.deleted_at is None

    def test_offering_row_nullable_fields(self) -> None:
        row = OfferingRow(
            tenant_id="t1",
            name="My Offering",
        )
        assert row.name == "My Offering"
        assert row.description is None
        assert row.value_proposition is None
        assert row.deleted_at is None

    def test_lead_row_defaults(self) -> None:
        row = LeadRow(
            tenant_id="t1",
            campaign_id="c1",
            company_name="Acme Corp",
        )
        # SQLAlchemy column default (stage="prospect") applies at flush
        assert row.score is None
        assert row.company_name == "Acme Corp"
        assert row.domain is None

    def test_event_row_fields(self) -> None:
        row = EventRow(
            id="e1",
            tenant_id="t1",
            event_type="lead.discovered",
            payload={"count": 5},
        )
        assert row.event_type == "lead.discovered"
        assert row.payload == {"count": 5}
        assert row.campaign_id is None
        assert row.lead_id is None

    def test_message_row_defaults(self) -> None:
        row = MessageRow(
            tenant_id="t1",
            campaign_id="c1",
            lead_id="l1",
            channel="email",
            body="Hello",
        )
        # SQLAlchemy column defaults (status, sequence_number) apply at flush
        assert row.subject is None
        assert row.sent_at is None
        assert row.external_message_id is None

    def test_all_table_names_are_unique(self) -> None:
        table_names = {
            TenantRow.__tablename__,
            OfferingRow.__tablename__,
            CampaignRow.__tablename__,
            LeadRow.__tablename__,
            MessageRow.__tablename__,
            ReplyRow.__tablename__,
            EventRow.__tablename__,
        }
        assert len(table_names) == 7
