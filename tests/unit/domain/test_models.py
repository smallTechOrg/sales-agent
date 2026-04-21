# Phase-1 gate — domain model tests
# Spec: spec/engineering/phases.md § Phase 1
from __future__ import annotations

import pytest
from pydantic import ValidationError

from zer0.domain.config import (
    ApprovalMode,
    Channel,
    CompanySizeRange,
    OutreachConfig,
    OutreachTemplates,
    QualificationConfig,
    RubricCriterion,
)
from zer0.domain.lead import (
    LeadSource,
    LeadStage,
    PerCriterionScore,
    QualifiedLead,
    RawLead,
)
from zer0.domain.outreach import MessageStatus, Sentiment


class TestLeadEnums:
    def test_lead_stage_values(self) -> None:
        assert LeadStage.discovered == "discovered"
        assert LeadStage.qualified == "qualified"
        assert LeadStage.rejected == "rejected"
        assert LeadStage.approved == "approved"

    def test_lead_source_values(self) -> None:
        assert LeadSource.linkedin == "linkedin"
        assert LeadSource.web == "web"
        assert LeadSource.directory == "directory"


class TestRawLead:
    def test_minimal_construction(self) -> None:
        lead = RawLead(
            id="l1",
            campaign_id="c1",
            tenant_id="t1",
            url="https://example.com",
            source=LeadSource.web,
        )
        assert lead.id == "l1"
        assert lead.name is None
        assert lead.company is None

    def test_source_coercion_from_string(self) -> None:
        lead = RawLead(
            id="l1",
            campaign_id="c1",
            tenant_id="t1",
            url="https://x.com",
            source="linkedin",  # type: ignore[arg-type]
        )
        assert lead.source == LeadSource.linkedin


class TestQualifiedLead:
    def test_inherits_raw_lead_fields(self) -> None:
        lead = QualifiedLead(
            id="l1",
            campaign_id="c1",
            tenant_id="t1",
            url="https://x.com",
            source=LeadSource.web,
            score=80.0,
            per_criterion_scores=[PerCriterionScore(criterion_name="fit", score=80.0)],
            rationale="Strong fit",
        )
        assert lead.score == 80.0
        assert lead.url == "https://x.com"
        assert lead.company is None  # optional field from RawLead


class TestConfigValidation:
    def test_approval_mode_enum_values(self) -> None:
        assert ApprovalMode.full_auto == "full_auto"
        assert ApprovalMode.approve_all == "approve_all"

    def test_channel_enum_values(self) -> None:
        assert Channel.email == "email"
        assert Channel.whatsapp == "whatsapp"

    def test_company_size_range_min_must_be_at_least_1(self) -> None:
        with pytest.raises(ValidationError):
            CompanySizeRange(min=0, max=100)

    def test_rubric_criterion_weight_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            RubricCriterion(name="fit", description="desc", weight=0.0)

    def test_rubric_criterion_weight_must_not_exceed_1(self) -> None:
        with pytest.raises(ValidationError):
            RubricCriterion(name="fit", description="desc", weight=1.1)

    def test_qualification_config_requires_at_least_one_criterion(self) -> None:
        with pytest.raises(ValidationError):
            QualificationConfig(
                rubric_criteria=[],
                score_threshold=50.0,
                disqualifying_signals=[],
            )

    def test_outreach_config_requires_at_least_one_channel(self) -> None:
        with pytest.raises(ValidationError):
            OutreachConfig(
                channels_enabled=[],
                tone="professional",
                language_default="en",
                templates=OutreachTemplates(first_touch="Hi"),
            )


class TestOutreachEnums:
    def test_message_status_values(self) -> None:
        assert MessageStatus.drafted == "drafted"
        assert MessageStatus.sent == "sent"
        assert MessageStatus.pending_approval == "pending_approval"

    def test_sentiment_values(self) -> None:
        assert Sentiment.positive == "positive"
        assert Sentiment.negative == "negative"
        assert Sentiment.neutral == "neutral"
