# Phase-3 gate — observability tests
# Spec: spec/engineering/phases.md § Phase 3
from __future__ import annotations

from unittest.mock import MagicMock

from zer0.observability.events import write_event


class TestWriteEvent:
    def test_no_db_does_not_raise(self) -> None:
        write_event(
            db=None,
            event_type="test.noop",
            payload={"n": 1},
            tenant_id="t1",
        )

    def test_no_db_returns_none(self) -> None:
        result = write_event(db=None, event_type="x", payload={}, tenant_id="t1")
        assert result is None

    def test_with_db_calls_add_and_flush(self) -> None:
        db = MagicMock()
        write_event(
            db=db,
            event_type="lead.found",
            payload={"count": 3},
            tenant_id="t1",
            campaign_id="c1",
        )
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_with_db_adds_event_row_with_correct_fields(self) -> None:
        from zer0.db.models import EventRow

        db = MagicMock()
        write_event(
            db=db,
            event_type="lead.qualified",
            payload={"score": 88},
            tenant_id="t1",
            campaign_id="c1",
            lead_id="l1",
        )
        row = db.add.call_args[0][0]
        assert isinstance(row, EventRow)
        assert row.event_type == "lead.qualified"
        assert row.tenant_id == "t1"
        assert row.campaign_id == "c1"
        assert row.lead_id == "l1"

    def test_with_db_optional_fields_default_to_none(self) -> None:
        from zer0.db.models import EventRow

        db = MagicMock()
        write_event(db=db, event_type="x", payload=None, tenant_id="t1")
        row = db.add.call_args[0][0]
        assert row.campaign_id is None
        assert row.lead_id is None
        assert row.config_snapshot is None

    def test_with_db_payload_defaults_to_empty_dict(self) -> None:
        from zer0.db.models import EventRow

        db = MagicMock()
        write_event(db=db, event_type="x", payload=None, tenant_id="t1")
        row = db.add.call_args[0][0]
        assert row.payload == {}
