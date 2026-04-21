---
description: "Scaffold a new capability spec file in spec/product/04-capabilities/ using the standard template. Run spec-new-capability workflow."
agent: agent
argument-hint: "[capability-slug]"
tools: [read, search, edit]
---

Run the workflow defined in
[`spec/engineering/workflows/spec-new-capability.md`](../../spec/engineering/workflows/spec-new-capability.md).

If the user passed a slug argument, treat it as the capability slug: $ARGUMENTS.
