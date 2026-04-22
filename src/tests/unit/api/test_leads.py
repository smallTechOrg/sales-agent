# Unit tests for leads API helpers
# Spec: spec/product/09-api.md — /leads
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from zer0.api.leads import LeadOut, LeadPatch, _row_to_out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 4, 22, 9, 0, 0)


def _make_lead_row(**kwargs) -> MagicMock:
    """Return a MagicMock that mimics the current LeadRow column set."""
    defaults = dict(
        id="lead-1",
        tenant_id="tenant-1",
        campaign_id="camp-1",
        link_id="link-1",
        stage="prospect",
        company_name="Acme Corp",
        domain="acme.com",
        industry="SaaS",
        headcount_range="50-200",
        business_type="B2B",
        research_summary="Fast-growing SaaS company.",
        signals=["hiring", "growth"],
        score=Decimal("82.5"),
        per_criterion_scores=[{"criterion": "fit", "score": 85}],
        rationale="Strong ICP match.",
        rejection_reason=None,
        detected_language="en",
        blocked_at=None,
        created_at=_NOW,
        updated_at=_NOW,
    )
    defaults.update(kwargs)
    row = MagicMock()
    for k, v in defaults.items():
        setattr(row, k, v)
    return row


# ---------------------------------------------------------------------------
# Tests: _row_to_out field mapping
# ---------------------------------------------------------------------------


class TestRowToOut:
    def test_maps_all_current_fields(self) -> None:
        row = _make_lead_row()
        out = _row_to_out(row)

        assert out.id == "lead-1"
        assert out.tenant_id == "tenant-1"
        assert out.campaign_id == "camp-1"
        assert out.link_id == "link-1"
        assert out.stage == "prospect"
        assert out.company_name == "Acme Corp"
        assert out.domain == "acme.com"
        assert out.industry == "SaaS"
        assert out.headcount_range == "50-200"
        assert out.business_type == "B2B"
        assert out.research_summary == "Fast-growing SaaS company."
        assert out.signals == ["hiring", "growth"]
        assert out.score == pytest.approx(82.5)
        assert out.per_criterion_scores == [{"criterion": "fit", "score": 85}]
        assert out.rationale == "Strong ICP match."
        assert out.rejection_reason is None
        assert out.detected_language == "en"
        assert out.blocked_at is None
        assert out.created_at == _NOW
        assert out.updated_at == _NOW

    def test_score_none_stays_none(self) -> None:
        row = _make_lead_row(score=None)
        out = _row_to_out(row)
        assert out.score is None

    def test_score_decimal_converted_to_float(self) -> None:
        row = _make_lead_row(score=Decimal("75.123"))
        out = _row_to_out(row)
        assert isinstance(out.score, float)
        assert out.score == pytest.approx(75.123)

    def test_nullable_fields_accept_none(self) -> None:
        row = _make_lead_row(
            link_id=None,
            company_name=None,
            domain=None,
            industry=None,
            headcount_range=None,
            business_type=None,
            research_summary=None,
            signals=None,
            per_criterion_scores=None,
            detected_language=None,
        )
        out = _row_to_out(row)
        assert out.link_id is None
        assert out.company_name is None
        assert out.domain is None


class TestLeadOutSchema:
    def test_has_no_stale_name_field(self) -> None:
        assert "name" not in LeadOut.model_fields

    def test_has_no_stale_company_field(self) -> None:
        assert "company" not in LeadOut.model_fields

    def test_has_no_stale_url_field(self) -> None:
        assert "url" not in LeadOut.model_fields

    def test_has_no_stale_source_field(self) -> None:
        assert "source" not in LeadOut.model_fields

    def test_has_no_stale_contact_email_field(self) -> None:
        assert "contact_email" not in LeadOut.model_fields

    def test_has_no_stale_contact_role_field(self) -> None:
        assert "contact_role" not in LeadOut.model_fields

    def test_has_current_company_name_field(self) -> None:
        assert "company_name" in LeadOut.model_fields

    def test_has_current_domain_field(self) -> None:
        assert "domain" in LeadOut.model_fields

    def test_has_current_signals_field(self) -> None:
        assert "signals" in LeadOut.model_fields

    def test_has_blocked_at_field(self) -> None:
        assert "blocked_at" in LeadOut.model_fields


class TestLeadPatchSchema:
    def test_has_no_stale_contact_email_field(self) -> None:
        assert "contact_email" not in LeadPatch.model_fields

    def test_has_no_stale_contact_role_field(self) -> None:
        assert "contact_role" not in LeadPatch.model_fields

    def test_has_stage_field(self) -> None:
        assert "stage" in LeadPatch.model_fields

    def test_has_blocked_field(self) -> None:
        assert "blocked" in LeadPatch.model_fields

    def test_all_fields_optional(self) -> None:
        patch = LeadPatch()
        assert patch.stage is None
        assert patch.blocked is None
