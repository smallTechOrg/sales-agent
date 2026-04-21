# Capabilities

**Status:** DRAFT

Each file in this directory describes one discrete behaviour of Zer0 using the
standard template. Read the template first, then each file.

---

## Template

Every capability file uses this structure, in order:

1. **Purpose** — one or two sentences.
2. **Trigger** — what initiates this capability.
3. **Behavior** — numbered steps describing observable behaviour (not implementation).
4. **Inputs** — config keys, state reads, external data.
5. **Outputs** — side effects, state writes, API calls.
6. **Failure modes** — named failure classes and how the system responds.
7. **Out of scope** — explicit non-behaviours.

---

## Index

| File | Capability |
|---|---|
| [`01-discovery.md`](01-discovery.md) | Find raw leads from external sources |
| [`02-enrichment.md`](02-enrichment.md) | Research and enrich a raw lead |
| [`03-qualification.md`](03-qualification.md) | Score and accept/reject an enriched lead |
| [`04-outreach.md`](04-outreach.md) | Draft and send the first-touch message |
| [`05-follow-up.md`](05-follow-up.md) | Send cadenced follow-up messages |
| [`06-reply-handling.md`](06-reply-handling.md) | Detect and classify inbound replies |
