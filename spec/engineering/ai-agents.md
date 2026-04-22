# AI Agent Instructions

**Scope:** all AI coding assistants working in this repository (Claude Code, GitHub Copilot, OpenAI/Codex agents, and any future tool).

This is the single source of truth for how AI agents should behave in this repo. Tool-specific entry points (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.claude/`) are thin integration shims that point here — they contain no rules of their own.

---

## 1. Product

This is **Zer0** — an autonomous multi-tenant sales agent platform. Before writing anything, read:

- [`spec/product/01-vision.md`](../product/01-vision.md) — what Zer0 is, the four-stage loop, and success criteria.
- [`spec/product/02-architecture.md`](../product/02-architecture.md) — layered architecture, domain models, tools, config resolution.

---

## 1a. Session-start checklist & Before Every Reply — do this first, every time

Every time an AI agent starts or resumes a session in this repo, before reading any task description or writing any code, it **must** execute the following steps in order:

1. **Read this file** (`spec/engineering/ai-agents.md`) in full. Not just the section that seems relevant — the whole file. This is non-negotiable even when resuming from a conversation summary, because summaries do not carry forward standing obligations.
2. **Run `git status`** to see the true state of the working tree. If there are modified or untracked files that represent completed work from a prior session, commit and push them before doing anything else.
3. **Confirm a PR is open** for the current branch (`gh pr view` or equivalent). If no PR exists and work has already been pushed, open one now.
4. **Check README staleness** against any changes already in the branch that have not yet triggered a README update (repo layout, CLI commands, quick-start steps, graph topology).
5. **Open or resume a session report** — see §1b.

Rationale: context windows end abruptly. A session summary compresses history and drops standing obligations (README, commit, PR). The checklist exists precisely because the summary cannot be trusted to carry them forward.

---

## 1b. Session report — mandatory running log

Every AI agent session **must** produce a structured report file that a second agent (or human) can read to understand exactly what was done and resume from the middle without re-reading the conversation.

### File location and naming

```
reports/sessions/YYYY-MM-DD-HHMMSS-<branch>.md
```

Example: `reports/sessions/2026-04-21-143000-feat-implementation.md`

Create this file **at the start of the session** (step 5 in §1a). If a report file already exists for the current branch from a recent session (same day), append to it rather than creating a new one.

### Required structure

```markdown
# Session Report — <branch> — <date>

**Agent:** Claude Code / GitHub Copilot / <tool name>
**Started:** <ISO timestamp>
**Branch:** <branch name>
**Goal:** <one-sentence description of the task from the user>

## Completed steps

<!-- append one entry per logical action, newest at the bottom -->

### [HH:MM] <Action title>
- **What:** <one-sentence description of what was done>
- **Files:** <list of files created/modified/deleted>
- **Spec:** <spec file(s) that authorise this change, if any>
- **Result:** success | failed | partial

## Pending / next steps

<!-- keep this section up to date — another agent must be able to pick up from here -->

- [ ] <next task>
- [ ] <next task>

## Blockers

<!-- anything that stopped progress or required a decision -->
```

### Update rules

| Moment | Required update |
| ------ | --------------- |
| After completing any spec change | Add a "Completed steps" entry + update "Pending" |
| After completing any code change | Add a "Completed steps" entry + update "Pending" |
| Before every user-facing reply that describes completed work | Verify the report is current; if not, update it first |
| On session end | Mark all finished items, fill in any remaining "Pending" items |

### Commit and push rules

The session report file **is not committed separately**. It travels in the same commit as the code or spec change it documents — one commit, one report update. Do not leave the report uncommitted when the working tree is otherwise clean.

If the session ends with no code changes (research-only), commit the report file alone.

### Resumption protocol

When an agent starts a session and finds an existing report for the current branch:

1. Read the report top to bottom.
2. Identify the last "Completed steps" entry — that is the true state of the branch.
3. Pick up from the first unchecked item in "Pending / next steps".
4. Do **not** re-derive state from the git log alone — the report captures decisions and context that the log does not.

The report is the handoff contract between sessions. An agent that does not maintain it is breaking continuity for every subsequent agent.

---

## 2. Spec first

Rule: [`spec/engineering/spec-driven.md`](spec-driven.md)

- Before writing or changing code, write or update the relevant spec file.
- If there is no spec file for what you are building, create one.
- Spec and code changes travel in the same commit.
- Drift between spec and code is a bug. The spec wins.

### Spec files must always be read in full — never skipped, never summarised

Spec files in `spec/product/` and `spec/engineering/` are **never** treated as background context to be abbreviated in any summary or session handoff. When any spec file is relevant to a change:

1. **Read it in full** with `read_file` before touching any code. Reading "enough of it" is not sufficient.
2. **Never act on a conversation summary's description of a spec file.** Summaries lose precision. Re-read the actual file.
3. **Every change to schema, API shape, graph behaviour, or a product concept must land in the spec first, in the same session, before the first code edit.**

Failure mode this blocks: an agent reads a partial summary of the data-model spec, writes a migration and ORM model, and the spec never gets updated — leaving the authoritative description out of date with no record of the decision.

The spec is the contract. Code that was written without a spec change is unreviewed by definition — there is no authoritative description of what it is supposed to do.

---

## 3. Git workflow

Rule: [`spec/engineering/commits.md`](commits.md)

- Commit every logical unit of work. Do not accumulate uncommitted changes.
- Every commit goes on a feature branch — never directly to `main`.
- Every feature branch must have an open PR before the session ends.
- Commit message: ≤70 char subject, imperative mood, body references the spec file that authorises the change.
- PR body: Summary (2–3 bullets) + Test plan checklist + spec file(s) affected.

### HARD STOP — before every single reply

This rule fires **before any reply, at any point in the session, without exception**. It does not only fire at the end — it fires every time before the agent writes a message to the user.

```
BEFORE REPLYING:
  1. Run `git status`
  2. If any file is modified, staged, or untracked and represents completed work:
       git add <files>
       git commit -m "<message>"
       git push
  3. Run `git status` again — must show "nothing to commit, working tree clean"
  4. Only then write the reply
```

Failure mode this blocks: an agent completes real work, tells the user "done", and the work is not committed. This happens most often when:
- Tests pass and the agent replies immediately without committing the fixes.
- The agent fixes multiple files in one task and only commits the "main" ones.
- The session is long and the agent forgets prior edits are still dirty.

**If the reply describes work as completed and `git status` is not clean, the reply is wrong. Fix the tree first.**

### Mandatory commit-and-push checkpoints — non-negotiable

An AI agent **must** commit **and push** at **each** of the following moments. Not at the end of the session. At each checkpoint, with no exceptions:

| Checkpoint | What to do |
| ---------- | ---------- |
| After completing any spec change | `git add <spec files> && git commit && git push` immediately. |
| After completing any code change | `git add <src files> && git commit && git push` immediately. |
| After completing a task that was in the todo list | Mark the todo completed, commit **and push** before moving to the next todo. |
| After any test file is added or modified | Treat as a code change — commit and push immediately. |
| Before responding to the user after completing work | Run `git status`. If not clean, commit and push before replying. |

**Every commit is pushed immediately.** There is no "push at the end" — pushing after every commit means interrupted sessions, browser refreshes, and second agents always see the true state of the branch.

**Test files are code.** Modifying `tests/` is a code change. The rule applies.

**The working tree must be clean before any user-facing reply that describes completed work.** If `git status` shows modified or untracked files that represent completed work, that is a bug in the agent's behaviour — fix it by committing before replying.

This rule exists because leaving uncommitted work in the tree means the work is lost if the session is interrupted, and it misleads the user about the state of the repository.

### Replies must include the commit reference when work is described as complete

When a reply says something is "done", "complete", "passing", "fixed", or equivalent, it **must** include the short commit SHA or the output of `git log --oneline -1`. This is not optional formatting — it is evidence that the commit happened. A reply that says "72 tests pass" without a commit SHA does not satisfy the commit rule.

Example of a valid completion reply:
```
72 tests pass. Committed: abc1234 fix: update stale unit tests for new pipeline
```

### Session-end sweep — before considering any reply "done"

Before writing a reply that describes work as completed, an AI agent **must** verify every item below. If any item fails, fix it first — then reply.

| Check | Command | Pass condition |
| ----- | ------- | -------------- |
| Working tree is clean | `git status` | `nothing to commit, working tree clean` |
| Branch is pushed | `git log origin/<branch>..HEAD` | empty (no commits ahead of remote) |
| PR is open | `gh pr view` | PR exists, not draft unless WIP |
| README is current | Review §10 trigger table against changes in branch | No stale sections |
| Session report is current | Read `reports/sessions/<branch>.md` | All completed work has a log entry; "Pending" reflects true remaining work |

This sweep is not optional when working is described as finished. A reply that says "done" with a dirty tree, unpushed commits, no PR, or a stale README is incorrect regardless of the quality of the code change.

### Integration testing — process hygiene

When an AI agent runs servers (API, UI dev server, workers) as part of verifying a change, it **must**:

1. **Start on a free port.** Before starting any process, confirm the port is free (`lsof -i :<port> | grep LISTEN`). Do not assume a port is free.
2. **Record every PID or process name** started during the session.
3. **Stop everything before replying.** After completing the verification, kill every process the agent started — before writing the reply to the user. Use `pkill -f "<process pattern>"` or kill by PID. Confirm the port is clear afterwards.
4. **Never leave a background server running** in the user's terminal after the agent's turn ends. The user did not ask for a persistent process; they asked for a verified change.

The session-end sweep (above) must include: `lsof -i :<ports used> | grep LISTEN || echo "all clear"` — all ports must show "all clear" before the reply is sent.

Rationale: background processes the user did not knowingly start clutter their environment, consume resources, hold ports, and create confusion when they start their own servers.

---

## 4. Code style

Rule: [`spec/engineering/code-style.md`](code-style.md)

- Python 3.12, Pydantic v2, strict mypy.
- Types at every module boundary — no raw dicts crossing layers.
- Tools are pure-ish functions: typed input → typed output → log via `observability`.
- Prompts live in `src/zer0/prompts/` as `.md` files with `{{variable}}` placeholders. Never inline in Python.
- The graph is thin — `graph/agent.py` ≤ 50 lines. All behaviour in node and tool functions.

---

## 5. Secret hygiene

Rule: [`spec/engineering/secret-hygiene.md`](secret-hygiene.md)

- No secrets in code. Use `.env` via `pydantic-settings`.
- Never commit `.env` or any file containing a credential.

---

## 6. Tenant isolation

Rule: [`spec/engineering/tenant-isolation.md`](tenant-isolation.md)

- `tenant_id` is non-nullable on every database table.
- Every query, tool call, and log entry is scoped to a tenant.
- No data crosses tenant boundaries.
- `ConfigResolver` merges Campaign overrides onto Offering defaults — no node or tool reads raw config models directly.

---

## 7. Workflows (for structured tasks)

| Task | Workflow |
| ---- | -------- |
| Multi-file change | [`spec/engineering/workflows/plan.md`](workflows/plan.md) |
| Audit spec/code drift | [`spec/engineering/workflows/spec-check.md`](workflows/spec-check.md) |
| Review a change for coherence | [`spec/engineering/workflows/spec-review.md`](workflows/spec-review.md) |
| Review a plan before executing | [`spec/engineering/workflows/plan-review.md`](workflows/plan-review.md) |
| Scaffold a new capability spec | [`spec/engineering/workflows/spec-new-capability.md`](workflows/spec-new-capability.md) |
| Audit for duplicate facts | [`spec/engineering/workflows/dry-audit.md`](workflows/dry-audit.md) |
| Validate markdown links | [`spec/engineering/workflows/link-validate.md`](workflows/link-validate.md) |

---

## 8. Phased implementation

Rule: [`spec/engineering/phases.md`](phases.md)

Every implementation — initial build, new capability, refactor — follows the 10-phase model ordered by the module dependency graph. The non-negotiable rules:

- **Never skip a phase.** Build and test each layer before the layer above it.
- **Gate before proceeding.** The gate tests for a phase must be green before writing code in the next phase.
- **Tests travel with code.** A commit adding a source file without its matching test file fails the gate. No exceptions.
- **One commit per phase.** Subject prefix: `phase-N:` (e.g. `phase-1: domain models + tests`).
- **Backfill when out of order.** If a module was implemented without tests (e.g. a bulk implementation), the next PR must add the missing phase tests before any new dependent code is added.

Phase ordering (dependency-first):

| Phase | Module | Depends on |
|---|---|---|
| 0 | Skeleton + tooling | — |
| 1 | `domain/` | 0 |
| 2 | `config/` | 1 |
| 3 | `observability/` | 1 |
| 4 | `llm/` + `prompts/` | 2 |
| 5 | `db/` | 1, 2 |
| 6 | `tools/` | 1, 3, 4 |
| 7 | `graph/` | 1, 3, 4, 5, 6 |
| 8 | `api/` | 1, 5, 7 |
| 9 | `cli/` | 2, 5, 7 |
| 10 | Integration | all |
| 11 | `ui/` (Next.js dashboard) | 8 |

---

## 9. Keeping tool files in sync

`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, and `.claude/` are integration shims. They must never contain rules. If you need to add or change a rule, add it here in `spec/engineering/ai-agents.md` (or another `spec/engineering/` file) and update the pointer in the shim if needed. The shims stay lean — they exist only so each tool can find this file.

---

## 10. Keeping README.md current

`README.md` at the repo root is the first thing any reader sees. It must accurately reflect the current state of the product.

**An AI agent must update `README.md` whenever any of the following changes:**

| What changed | What to update in README |
| ------------ | ------------------------ |
| Repo layout (new module, removed module, path changed) | `## Repo layout` section |
| CLI commands added, removed, or renamed | `## CLI commands` section |
| Quick-start steps changed (new env vars, new install steps) | `## Quick start` section |
| Agent graph topology changed (nodes, edges) | `## The agent pipeline` section |
| Product purpose or scope changed | Opening description |
| A new phase completes that introduces a runnable component (server, UI, worker…) | Add a `## <Component>` section covering: how to install, how to run in dev, how to build/start in prod, and a link to the full spec file |

The last row is the most commonly missed. When you build something a developer needs to run, the README must tell them how. "Runnable component" means: anything that binds a port, opens a browser, starts a background process, or requires its own install step. The absence of a README section for a runnable component is a spec violation even if no other row in the table was triggered.

The README is **never** authoritative — all detail lives in `spec/`. The README is a navigational summary that points to `spec/`. It must not duplicate spec content; it must link to it.

If a change lands that makes the README stale and you do not update it in the same commit **and push**, that is a spec violation (same class as code/spec drift).

The README update travels in the same commit as the code or layout change that triggered it — not in a separate follow-up commit, and not left staged. Use the session-end sweep (§3) to verify no README debt remains before replying.
