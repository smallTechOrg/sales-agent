# Workflow: scaffold a new capability spec

Create a new capability spec file at `spec/product/04-capabilities/<slug>.md` following the
capability template defined in [`../../README.md`](../../README.md#capability-template).

## Procedure

1. If no slug argument was provided, ask the user for:
   - The capability slug (lowercase-kebab-case, e.g. `research-lead`, `draft-email`)
   - The one-sentence purpose
   - The component name (e.g. `ResearchLead`)
   - The trigger type (agent decision / manual CLI)

2. Check that `spec/product/04-capabilities/<slug>.md` does not already exist. Refuse if it does.

3. Create the file using the capability template structure. Status starts as `DRAFT`. Fill in what the user provided; leave `TODO` markers in every other section.

4. After writing the file, update any capability list in `spec/product/02-architecture.md` if appropriate.

5. Do **not** write any code. Spec-first: code comes later, after the spec is reviewed.

## Reminders

- Failure modes must cover auth errors, rate limits, external API failures, and malformed responses at minimum.
- Numbered behaviour steps describe **observable** behaviour, not implementation detail.
- "Out of scope" should be explicit — it prevents scope creep better than silence.
