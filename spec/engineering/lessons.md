# LESSONS — Mistakes agents must never repeat

**Mandatory reading at the start of every session, before any code or spec work.**
Every entry is a real mistake made by an AI agent in this repo. Never repeat them.

---

## L-001 — Never finish a logical unit of work without committing and pushing

**Mistake:** Completed a multi-file change spanning spec updates, migrations, ORM models,
domain models, tools, graph nodes, and API endpoints — across two sessions — and never
ran `git add`, `git commit`, or `git push`. The user had to ask for it explicitly. This
happened at least 10 times across multiple sessions.

**Rule (from `spec/engineering/commits.md`):**
> "AI agents: commit AND push per logical unit. When an AI agent completes a logical
> unit of work (tests pass, lint clean), it must commit **and immediately push** before
> starting the next unit. Never leave completed work uncommitted or unpushed."

**Mandatory sequence after every logical unit:**
```bash
git add -A
git commit -m "<type>: <subject>"
git push
```

If `run_in_terminal` is not available this session: state it once, stop, wait for restart. **Never give the user a list of commands to run manually.**

---

## L-002 — No terminal = no tests, no git — say so once, then stop

**Mistake:** Wrote code across many files without verifying it runs because `run_in_terminal`
was not available. Did not tell the user upfront.

**Rule:** At the start of every session, run `tool_search_tool_regex(pattern="run_in_terminal|terminal")`.
- If returned → use it for all git, test, and lint commands immediately after every change.
- If not returned → say once: "run_in_terminal is not available — VS Code restart will fix it." Then **stop**. Do not ask the user to run anything. Do not list commands. Never.

---

## L-003 — Always create a PR after pushing, not just a commit

**Mistake:** Even when reminded to commit, stopped at `git push` without creating a pull request.

**Rule:** After pushing a feature branch, immediately run:
```bash
gh pr create --title "<same as commit subject>" \
  --body "## Summary
- <bullet>

## Test plan
- [ ] <step>" \
  --base main
```

---

## L-004 — Search for run_in_terminal at session start; never assume unavailability

**Mistake:** Claimed `run_in_terminal` was unavailable without searching for it. The tool
exists and has been working for months in this repo.

**Rule:** First action of every session:
```
tool_search_tool_regex(pattern="run_in_terminal|terminal")
```
Never assert the tool is unavailable without running this search first. If the search returns
it, use it. If not, state that the search returned nothing.

---

## L-005 — Write the session report and prompt log in real time, not at end of session

**Mistake:** Did not create or update `reports/sessions/<date>-<branch>.md` during the
session. Did not append prompt log rows after each user turn.

**Rule (from `spec/engineering/ai-agents.md` §1b):**
- Create the session report file as the **first action** of the session.
- After **every user prompt**, append a row to the Prompt log table immediately.
- After **every code or spec change**, add a Completed steps entry.
- Commit the report with the code it documents — never leave it uncommitted.

---

## L-006 — Duplicate ORM classes crash SQLAlchemy at import time

**Mistake:** `src/zer0/db/models.py` ended up with `LinkLeadsRow` and `CampaignRunRow`
defined twice. SQLAlchemy raises `InvalidRequestError: Table 'link_leads' is already
defined` at import time.

**Rule:** Before adding a new class to `models.py`, `grep_search` the file for the class
name first. If it already exists, edit it — never append a duplicate.

---
