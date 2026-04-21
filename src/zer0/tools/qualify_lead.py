"""qualify_lead tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  EnrichedLead + QualificationConfig
Output: QualifiedLead | RejectedLead
"""

from __future__ import annotations

import json

from zer0.domain import EnrichedLead, QualifiedLead, RejectedLead
from zer0.domain.config import QualificationConfig, ResolvedConfig
from zer0.domain.lead import PerCriterionScore
from zer0.llm.client import LLMClient


def qualify_lead(
    *,
    lead: EnrichedLead,
    qualification_config: QualificationConfig,
    llm: LLMClient,
    config: ResolvedConfig,
) -> QualifiedLead | RejectedLead:
    """Score lead against rubric criteria. Returns QualifiedLead if score ≥ threshold."""
    system = llm.load_prompt("qualifier", config)
    criteria_desc = "\n".join(
        f"- {c.name} (weight {c.weight}): {c.description}"
        for c in qualification_config.rubric_criteria
    )
    user = (
        f"Company: {lead.company}\n"
        f"Summary: {lead.company_summary}\n"
        f"Role: {lead.contact_role}\n"
        f"Role summary: {lead.role_summary}\n"
        f"Signals: {', '.join(lead.recent_signals)}\n\n"
        f"Rubric criteria:\n{criteria_desc}\n\n"
        "Return JSON: {score: 0-100, per_criterion: [{name, score}], rationale: str, reject_reason: str|null}"
    )

    raw = llm.complete(system=system, user=user)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"score": 0, "per_criterion": [], "rationale": "", "reject_reason": "LLM parse error"}

    score: float = float(parsed.get("score", 0))
    per_scores = [
        PerCriterionScore(criterion_name=c["name"], score=float(c["score"]))
        for c in parsed.get("per_criterion", [])
    ]
    rationale: str = parsed.get("rationale", "")
    reject_reason: str | None = parsed.get("reject_reason")

    if score >= qualification_config.score_threshold and not reject_reason:
        return QualifiedLead(
            **lead.model_dump(),
            score=score,
            per_criterion_scores=per_scores,
            rationale=rationale,
        )

    return RejectedLead(
        **lead.model_dump(),
        rejection_reason=reject_reason or f"Score {score} below threshold {qualification_config.score_threshold}",
        per_criterion_scores=per_scores,
    )
