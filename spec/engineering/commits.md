# Rule: commits and pull requests

**Scope:** all git operations.

## Commit philosophy

- **One logical change per commit.** Not "one file per commit" — sometimes a logical change spans files (spec + code + test are often one change). Not "one commit per session" either — if you've done three things, make three commits.
- **Commit every hour.** If a task is done, commit it — don't batch a day's work into one commit. Frequent commits keep the diff reviewable and make `git revert` / `git bisect` precise tools instead of blunt ones.
- **AI agents: commit AND push per logical unit.** When an AI agent completes a logical unit of work (tests pass, lint clean), it must commit **and immediately push** before starting the next unit. Never leave completed work uncommitted or unpushed. See `spec/engineering/ai-agents.md §3` for the full checkpoint list.
- **Never amend published commits.** Create a new commit instead.
- **Never `--force` push to `main`.** Ask first for any branch.
- **Never `--no-verify`** to bypass a pre-commit hook. Fix the underlying issue.

## Message format

Subject line: ≤70 chars, imperative mood, no trailing period.

```
feat: add research_lead tool

Previously the agent had no way to enrich lead data before drafting email.
Per spec/product/02-architecture.md, tools are the agent's only way to
affect the world. This adds research_lead as the first tool.
```

Rules for the body:
- Wrap at 72 chars.
- Explain **why** more than **what** — the diff already shows what.
- Reference the spec file(s) that authorize the change.
- When fixing a bug, include repro or root cause in one sentence.
- When adding a feature, link the capability spec file.

## When the change touches the spec

If the change updates both spec and code, the commit message should call this out:

```
feat: add draft_email tool (spec + code)

spec/product/02-architecture.md now describes the draft_email tool.
Implementation follows.
```

Spec-only changes are fine as standalone commits and preferred when the spec is
evolving before implementation.

## Co-authorship

When an AI agent materially authored the change, attribute it:

- Claude Code: `Co-Authored-By: Claude <noreply@anthropic.com>`
- GitHub Copilot: note in the body.

Don't over-claim: trivial autocompletions don't warrant a trailer. A multi-file
refactor performed by an agent does.

## Pull requests

- PR title mirrors the commit subject style.
- PR body has a **Summary** (2–3 bullets) and **Test plan** (checklist).
- Link spec file(s) affected.
- Draft PRs are fine for "in progress"; mark ready only when tests pass and spec is updated.

### Size and cadence

- **Keep PRs small and focused.** Target p50 ≈ 100–150 lines changed. One feature per PR.
- **Squash-merge every PR.** `main` stays a linear history of one-commit-per-feature.
- **The squash commit message is the PR body.** Rewrite it to the spec-linking message format before merging.

## Branches

- `main` is the release branch.
- Feature branches: `feat/<short-slug>`.
- Fix branches: `fix/<short-slug>`.
- Spec-only branches: `spec/<short-slug>` — useful for iterating on a spec before implementation.

## What not to commit

The authoritative list is the repo's [`.gitignore`](../../.gitignore). For secrets specifically,
see [`secret-hygiene.md`](secret-hygiene.md). If you find yourself wanting to commit something
not covered, update `.gitignore` first.
