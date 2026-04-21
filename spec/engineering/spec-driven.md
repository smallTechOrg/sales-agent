# Spec-Driven Development

**Scope:** entire repository.

The spec is the source of truth. Code is a mechanical translation of the spec.

## The rule

1. **Spec first.** Before writing or changing code, write or update the relevant
   spec file. If there is no spec file for what you are building, create one.
2. **Code second.** Once the spec is clear and reviewed, translate it into code.
3. **Drift is a bug.** If code diverges from the spec, the spec wins — fix the
   code, or update the spec and note the intentional deviation.

## What counts as a spec change

- Adding a new behaviour the product did not previously have.
- Changing how an existing behaviour works.
- Removing a behaviour.
- Renaming a concept across the system.

## What does NOT require a spec change first

- Bug fixes that make code match the existing spec.
- Refactors that do not change observable behaviour.
- Test additions.

## How to find the right spec file

```
spec/
  product/   ← what the system does
  engineering/ ← how contributors write code
```

If the change affects what the system does → `product/`.
If the change affects how contributors write code → `engineering/`.

---

## Diagram standards for tech design specs

Every tech design spec (any file in `spec/product/` numbered 02 or higher) **must** include all of the diagram types listed below that are applicable to its subject matter. A spec review that finds a missing diagram is a blocking issue — it is treated the same as missing a requirement.

All diagrams are written in [Mermaid](https://mermaid.js.org/) and embedded as fenced code blocks (` ```mermaid `). GitHub renders them natively. No external diagram files.

### Required diagram types by subject

| Subject | Required diagrams |
| ------- | ----------------- |
| System / component design | System context diagram (actors + external systems), deployment/container diagram (runnable processes + storage) |
| Module structure | Module dependency graph (directed, showing import relationships) |
| Data / config flow | Sequence diagram for every critical path (config resolution, request lifecycle, async flows) |
| Database schema | Entity-relationship diagram (Mermaid `erDiagram`), state machine for any entity with a lifecycle (Mermaid `stateDiagram-v2`) |
| API design | API resource map (endpoint hierarchy), sequence diagrams for every non-trivial flow (auth, async operations, approval gates) |
| Agent / state machine | Full graph topology (nodes + edges + conditions), fan-out/fan-in diagrams for parallel sections, state machine for any looping or parking behaviour, end-to-end sequence showing every tool call in the critical path |

### Diagram quality bar

A diagram is acceptable if a new engineer can answer the following questions from it alone:
- **Context diagram:** who are the users? what external systems are touched? what data crosses each boundary?
- **Deployment diagram:** how many processes? what does each own? how do they communicate?
- **Sequence diagram:** what is the happy path? what are the two most important error / branch paths?
- **ER diagram:** what are the cardinality relationships? which fields are nullable?
- **State machine:** what are all valid transitions? what event triggers each transition? are there any terminal states?
- **Graph topology:** what is the entry point? what are the conditional branches? what are the terminal nodes?

### What not to do

- Do not use screenshots of diagrams from external tools. Diagrams live in the spec as source.
- Do not omit error paths from sequence diagrams to keep them short.
- Do not use a table where a diagram would communicate structure or flow more clearly.
- Do not copy a diagram from one spec to another — link to the canonical spec instead.
