# Vision

Status: DRAFT

## What Zer0 is

Zer0 is an autonomous AI sales agent that runs the top of the sales funnel end-to-end — from cold prospecting to booked conversation — without human involvement.

Given an ideal customer profile (ICP), Zer0 searches the open internet for companies and individuals that match, researches each lead in depth, scores them against the ICP, and then sends personalised outreach on behalf of the operator. The operator sees only qualified, contacted prospects — they never touch raw leads.

**Target user:** a founder, sales lead, or RevOps operator at a B2B company who wants a full-time SDR working 24/7 without headcount.

**Core value proposition:** Zer0 collapses four distinct SDR tasks (list building, research, qualification, outreach) into a single automated loop that runs continuously and improves its own targeting as it learns what converts.

## What Zer0 is NOT

- Not a CRM. Zer0 generates and contacts leads; it does not manage the ongoing relationship or pipeline stages after the first reply.
- Not a mass-blast email tool. Every message is researched and personalised to the individual — volume is a byproduct of automation, not the goal.
- Not a data vendor. Zer0 does not sell or export lead lists. Leads are ephemeral work product in service of outreach.
- Not a human replacement for complex deals. Zer0 hands off as soon as a lead responds positively; closing is the human's job.

## The four-stage loop

```
DISCOVER → RESEARCH → QUALIFY → OUTREACH
```

| Stage    | What happens                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------- |
| Discover | Agent searches the internet (web, LinkedIn, job boards, directories) for companies and contacts that match the ICP. |
| Research | Agent deep-dives each prospect: company context, role, recent signals (funding, hiring, news).    |
| Qualify  | Agent scores the lead against the ICP rubric. Leads below threshold are discarded.               |
| Outreach | Agent drafts and sends a personalised first-touch email (and optional follow-ups) on the operator's behalf. |

## Design principles

1. **Autonomy first.** The agent must be able to run the full loop without human checkpoints. Human review is opt-in, not required.
2. **Quality over volume.** A disqualified lead costs nothing to discard; a bad email costs deliverability and reputation. The qualifier must be conservative.
3. **Transparency.** Every decision — why a lead was discovered, why it was qualified or rejected, what was sent — is logged and inspectable.
4. **No magic.** Control flow must be explainable in 60 seconds. No framework black boxes.
5. **Typed at every boundary.** All data flowing between stages is a Pydantic model. No raw dicts.

## Success criteria

- Given an ICP, the agent discovers ≥ 20 qualified leads per hour of runtime without human input.
- Qualification precision ≥ 80%: at least 8 in 10 leads that pass the qualifier are considered genuinely relevant by a human reviewer.
- Outreach emails pass a human quality bar: specific to the company, relevant to the role, and not detectable as AI-generated boilerplate.
- The operator can inspect the full reasoning trace for any lead at any time.
- The system runs end-to-end from a single CLI command.

## Out of scope

- CRM sync, pipeline management, or deal tracking.
- Inbound lead handling.
- Calls, LinkedIn DMs, or any channel other than email (v1).
- Multi-tenant SaaS infrastructure, billing, or user accounts.
- A/B testing or deliverability optimisation (future).
