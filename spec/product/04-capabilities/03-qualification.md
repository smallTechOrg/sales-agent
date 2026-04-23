# Capability: Lead Qualification

**Status:** DRAFT

## Purpose

Score each researched lead against the campaign's ICP rubric and decide whether to accept or reject it.

## Trigger

`node_qualify` runs after `node_research`. It calls `qualify_lead` for each `Lead` with `stage == "research"`.

## Behavior

1. For each researched lead:
   a. Load `QualificationConfig.rubric_criteria` — a list of weighted ICP criteria.
   b. Render `qualifier.md` prompt with `lead.company_name`, `lead.research_summary`, `lead.signals`, and rubric.
   c. Call LLM (`qualify_lead`) to produce per-criterion scores and a final `total_score`.
   d. Compare `total_score` to `QualificationConfig.score_threshold`.
   e. If `total_score >= score_threshold`:
      - Set `lead.stage = "qualification"`; set `lead.score`, `lead.per_criterion_scores`, `lead.rationale`.
      - Emit `lead_qualified` event.
   f. If `total_score < score_threshold`:
      - Set `lead.stage = "rejected"`; set `lead.rejection_reason`.
      - Emit `lead_rejected` event.
2. After all leads processed, if no leads have `stage == "qualification"`:
   - Set `AgentState.error = "all_leads_rejected"`.
   - Transition to error handler.

## Inputs

| Key | Source |
|---|---|
| `leads` (stage == `research`) | `AgentState.leads` |
| `rubric_criteria` | `ResolvedConfig.qualification_config.rubric_criteria` |
| `score_threshold` | `ResolvedConfig.qualification_config.score_threshold` |
| `qualifier.md` prompt | `src/zer0/prompts/qualifier.md` |

## Outputs

| Output | Type |
|---|---|
| `AgentState.leads` | `stage` updated to `"qualification"` or `"rejected"` |
| `leads` DB rows | `stage`, `score`, `per_criterion_scores`, `rationale`, `rejection_reason` written |
| `events` DB rows | `lead_qualified` or `lead_rejected` |

## Company size — non-blocking rule

`ICP.company_size_range` is **optional**. If it is `None` (not configured), the qualifier MUST NOT penalise the lead for unknown headcount. Specifically:
- If `headcount_range` is `NULL` on the lead, pass the value as `"unknown"` in the prompt — do not treat as a criterion failure.
- If `company_size_range` is `None` in the ICP config, omit the company-size criterion from the rubric rendered to the LLM entirely.
- Automatic rejection solely on the basis of unknown or mismatched company size is **forbidden**.

## Failure modes

| Class | Response |
|---|---|
| LLM returns invalid score JSON | Log `qualification_parse_error`, treat as rejected |
| Score is outside 0–100 range | Clamp to 0 or 100, log warning |
| All leads rejected | Transition to `node_handle_error` |

## Out of scope

- Human review of qualification decisions — approval mode in v1 applies at the people-selection step, not qualification.
- Feedback loops that adjust rubric weights automatically.
