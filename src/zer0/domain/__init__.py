"""Domain package exports.

Import all domain models from here rather than from sub-modules directly.
"""

from zer0.domain.config import (
    ApprovalMode,
    Channel,
    CompanySizeRange,
    DiscoveryConfig,
    DiscoverySource,
    ICP,
    OutreachConfig,
    OutreachTemplates,
    QualificationConfig,
    ResolvedConfig,
    RubricCriterion,
)
from zer0.domain.contact import Contact
from zer0.domain.lead import (
    Lead,
    LeadStage,
    PerCriterionScore,
)
from zer0.domain.link import Link, LinkSource
from zer0.domain.outreach import (
    MessageStatus,
    OutreachDraft,
    Reply,
    Sentiment,
    SentMessage,
)

__all__ = [
    # config
    "ApprovalMode",
    "Channel",
    "CompanySizeRange",
    "DiscoveryConfig",
    "DiscoverySource",
    "ICP",
    "OutreachConfig",
    "OutreachTemplates",
    "QualificationConfig",
    "ResolvedConfig",
    "RubricCriterion",
    # lead
    "Contact",
    "Lead",
    "LeadStage",
    "Link",
    "LinkSource",
    "PerCriterionScore",
    # outreach
    "MessageStatus",
    "OutreachDraft",
    "Reply",
    "Sentiment",
    "SentMessage",
]
