"""qualify_lead tool.

Spec: spec/product/04-capabilities/03-qualification.md
Input:  Lead + QualificationConfig
Output: Lead (stage set to qualification or rejected, score/rationale populated)
"""

from __future__ import annotations

import json
import re

import structlog

from zer0.domain import Lead
from zer0.domain.config import QualificationConfig, ResolvedConfig
from zer0.domain.lead import LeadStage, PerCriterionScore
from zer0.llm.client import LLMClient

log = structlog.get_logger(__name__)


def _parse_llm_json(raw: str) -> dict:
    """Parse JSON from LLM output, stripping markdown fences if present."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def qualify_lead(
    *,
    lead: Lead,
    qualification_config: QualificationConfig,
    llm: LLMClient,
    config: ResolvedConfig,
) -> Lead:
    """Score lead against rubric criteria. Returns Lead with stage set to qualification or rejected."""
    system = llm.load_prompt("qualifier", config)
    criteria_desc = "\n".join(
        f"- {c.name} (weight {c.weight}): {c.description}"
        for c in qualification_config.rubric_criteria
    )
    user = (
        f"Company: {lead.company_name}\n"
        f"Domain: {lead.domain}\n"
        f"Industry: {lead.industry}\n"
        f"Headcount: {lead.headcount_range}\n"
        f"Business type: {lead.business_type}\n"
        f"Research summary: {lead.research_summary}\n"
        f"Signals: {', '.join(lead.signals)}\n\n"
        f"Rubric criteria:\n{criteria_desc}\n\n"
        "Return JSON: {score: 0-100, per_criterion: [{name, score}], rationale: str, reject_reason: str|null}"
    )

    raw = llm.complete(system=system, user=user)

    try:
        parsed = _parse_llm_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("qualify.parse_error", lead_id=lead.id, error=str(exc), raw=raw[:200])
        parsed = {"score": 0, "per_criterion": [], "rationale": "", "reject_reason": "LLM parse error"}

    score: float = float(parsed.get("score", 0))
    per_scores = [
        PerCriterionScore(criterion_name=c["name"], score=float(c["score"]))
        for c in parsed.get("per_criterion", [])
    ]
    rationale: str = parsed.get("rationale", "")
    reject_reason: str | None = parsed.get("reject_reason")

    log.info(
        "qualify.scored",
        lead_id=lead.id,
        company=lead.company_name,
        score=score,
        threshold=qualification_config.score_threshold,
        reject_reason=reject_reason,
    )

    if score >= qualification_config.score_threshold and not reject_reason:
        return lead.model_copy(update={
            "stage": LeadStage.qualification,
            "score": score,
            "per_criterion_scores": per_scores,
            "rationale": rationale,
        })

    return lead.model_copy(update={
        "stage": LeadStage.rejected,
        "score": score,
        "per_criterion_scores": per_scores,
        "rejection_reason": reject_reason or f"Score {score} below threshold {qualification_config.score_threshold}",
    })
