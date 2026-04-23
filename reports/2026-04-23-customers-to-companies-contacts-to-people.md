# Plan: Rename Customers to Companies and Contacts to People

## Goal

Rename the persistent company-level `Customer` concept to `Company` and the person-level `Contact` concept to `Person` across spec, API, backend, graph state, and UI. Preserve existing behavior, tenant isolation, and cumulative company knowledge semantics while avoiding unrelated changes already present on `feat/cumulative-data`.

## Spec impact

- Update product nouns in the canonical spec files that currently define or expose `Customer` and `Contact` as system concepts: `spec/product/01-vision.md`, `spec/product/02-architecture.md`, `spec/product/04-capabilities/02-enrichment.md`, `spec/product/04-capabilities/04-outreach.md`, `spec/product/04-capabilities/05-follow-up.md`, `spec/product/04-capabilities/06-reply-handling.md`, `spec/product/04-capabilities/07-contact-discovery.md`, `spec/product/04-capabilities/08-approval.md`, `spec/product/07-data-model.md`, `spec/product/09-api.md`, `spec/product/10-agent-graph.md`, `spec/product/11-ui-dashboard.md`.
- Define the new canonical model explicitly: `Company` = tenant-wide persistent company knowledge record; `Person` = individual person associated with a lead/company and outreach.
- Rename API resources and object shapes in spec from `/customers` and `/contacts` to `/companies` and `/people`, and rename related identifiers from `customer_id` / `contact_id` to `company_id` / `person_id` where they refer to these domain entities.
- Decide in spec whether pipeline/state nouns also rename from `contacts` to `people` before implementation; if yes, carry that through `lead_stage`, graph state fields, approval flow text, and UI labels in the same change.
- Do not rename established sales terminology that is not the `Customer` entity, especially `ideal customer profile` / `ICP`, or tenancy text where `customer/brand` describes a tenant relationship rather than the `customers` table/resource.

## Engineering impact

- No engineering rule changes expected.
- Tenant isolation remains unchanged but the rename touches many tenant-scoped tables, FKs, queries, and events; every renamed identifier must continue to be filtered by `tenant_id`.
- Exclude unrelated dirty files and manifest drift from this change. In particular: do not fold in existing branch work unless required for the rename, and do not address missing `spec/product/06-cli.md` here.
- Treat generated UI build output as derivative: update source under `src/ui/src/` and only regenerate or refresh generated artifacts if the repo expects them to be tracked.

## Phases

1. **Spec rename and boundary pass**
   Test/gate: spec diff is internally consistent on `Company`/`Person`, preserves ICP wording, and leaves unrelated product terminology intact.

2. **Schema and persistence rename design**
   Test/gate: migration plan covers table names, FK columns, indexes, constraints, and historical cumulative-data semantics for `customers`/`contacts` without changing tenant scoping or dedup rules.

3. **Backend domain and API rename**
   Test/gate: domain models, ORM rows, route modules, request/response shapes, and graph state all use the new nouns consistently; route/resource alignment matches the updated API spec.

4. **Workflow and graph alignment**
   Test/gate: enrichment, people discovery, approval, outreach, follow-up, and reply-handling code paths still express the same behavior after the rename, including sibling-person outreach stopping and company-level cumulative research writes.

5. **UI route and language alignment**
   Test/gate: navigation, route segments, data hooks, detail screens, filters, and labels use `Companies` and `People` consistently, with no stale `/customers` or `/contacts` links in source UI code.

6. **Verification and cleanup pass**
   Test/gate: targeted search shows no remaining stale domain identifiers in intended source/spec surfaces except approved exclusions; unrelated dirty files remain untouched.

## Out of scope

- Fixing the missing `spec/product/06-cli.md` manifest drift.
- Unrelated branch changes already present on `feat/cumulative-data`.
- Broad terminology rewrites outside the `Customer`/`Contact` domain entities.
- Changing actual product behavior, approval rules, outreach logic, or tenant isolation policy beyond the semantic/resource rename.
- Backward-compatibility shims for old routes or payload names unless explicitly requested after the spec pass.

## Risks

- The rename spans schema, ORM, API, graph state, and UI at once; partial rollout will create immediate drift and broken references.
- Physical DB renames are riskier than label-only changes because this repo already has migrations and cross-table FKs for `customers`, `contacts`, `customer_id`, and `contact_id`.
- `contacts` may refer both to a domain entity and to a pipeline stage; if stage values also rename to `people`, that adds enum, API, UI filter, and data-migration scope.
- Generated UI artifacts and existing dirty files can produce noisy diffs; the execution should stay focused on source files and avoid accidental unrelated edits.