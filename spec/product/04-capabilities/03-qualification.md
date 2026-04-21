# Capability: Lead Qualification

**Status:** DRAFT

## Purpose

Score each enriched lead against the campaign's ICP rubric and decide whether to accept or reject it.

## Trigger

`node_qualify` runs after `node_research`. It calls `qualify_lead` for each `EnrichedLead`.

## Behavior

1. For each enriched lead:
   a. Load `QualificationConfig.rubric_criteria` — a list of weighted ICP criteria.
   b. Render `qualifier.md` prompt with lead data + rubric.
   c. Call LLM (`qualify_lead`) to produce per-criterion scores and a final `total_score`.
   d. Compare `total_score` to `QualificationConfig.score_threshold`.
   e. If `total_score >= score_threshold`:
      - Mark lead `stage = "qualified"`.
      - Append `QualifiedLead` to `AgentState.qualified_leads`.
      - Emit `lead_qualified` event.
   f. If `total_score < score_threshold`:
      - Mark lead `stage = "rejected"`.
      - Append `RejectedLead` with reason to `AgentState.rejected_leads`.
      - Emit `lead_rejected` event.
2. After all leads processed, if `AgentState.qualified_leads` is empty:
   - Set `AgentState.error = "all_leads_rejected"`.
   - Transition to error handler.

## Inputs

| Key | Source |
|---|---|
| `enriched_leads` | `AgentState.enriched_leads` |
| `rubric_criteria` | `ResolvedConfig.qualification_config.rubric_criteria` |
| `score_threshold` | `ResolvedConfig.qualification_config.score_threshold` |
| `qualifier.md` prompt | `src/zer0/prompts/qualifier.md` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.qualified_leads` | `list[QualifiedLead]` |
| `AgentState.rejected_leads` | `list[RejectedLead]` |
| `leads` DB rows | `stage = "qualified"` or `"rejected"` |
| `events` DB rows | `lead_qualified` or `lead_rejected` |

## Failure modes

| Class | Response |
|---|---|
| LLM returns invalid score JSON | Log `qualification_parse_error`, treat as rejected |
| Score is outside 0–100 range | Clamp to 0 or 100, log warning |
| All leads rejected | Transition to `node_handle_error` |

## Out of scope

- Human review of qualification decisions in v1 — approval mode applies to outreach, not qualification.
- Feedback loops that adjust rubric weights automatically.
