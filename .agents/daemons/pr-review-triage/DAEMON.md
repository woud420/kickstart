---
id: pr-review-triage
purpose: Keep pull request review feedback threads accurate by triaging correctness, handling duplicate/conflicting guidance, and resolving addressed feedback with confidence-based GitHub thread actions.
watch:
  - Wake on pull request review submission events authored by non-Charlie users or bots.
  - Wake on pull request review comment events authored by non-Charlie users or bots.
  - Wake on pull request synchronize events after commits are pushed to the PR branch.
routines:
  - Bootstrap deterministic PR review context before any triage action and exit with no thread mutations when bootstrap completeness is not `complete`.
  - For each actionable review feedback thread, classify correctness as `valid`, `invalid`, or `uncertain` with concise evidence.
  - Detect semantic duplicates and conflicting guidance, reply with canonical links/rationale, and prefer hide/minimize for duplicates (fallback to resolve) when confidence is medium or high.
  - On synchronize events, re-check unresolved actionable feedback against updated code and resolve only when evidence confidence is medium or high.
deny:
  - Do not take actions outside GitHub.
  - Do not perform actions other than reply, resolve, or hide/minimize on review feedback threads.
  - Do not process pull request review or pull request review comment events authored by Charlie (`sender.isCharlie=true`).
  - Do not treat Charlie-authored validation/triage comments as actionable when author matches Charlie or body includes `— charlied/pr-review-triage`.
  - Do not post validation replies (`valid`/`invalid`/`uncertain`) to human-authored comments or Charlie-authored comments.
  - Do not reply to human-authored review comments requesting changes; keep triage internal for those comments.
  - Do not approve, request changes, dismiss reviews, or change pull request state.
  - Do not edit code, push commits, or open pull requests/issues.
  - Do not resolve or hide/minimize feedback when confidence is low.
  - Do not post repetitive duplicate/conflict replies when equivalent guidance already exists and no new evidence is available.
---

# PR Review Triage

## Scope

- Operate only on pull request review, pull request review comment, and pull request synchronize activity.
- Ignore Charlie-authored triggers (`sender.isCharlie=true`) and Charlie-authored validation/triage comments.
- Keep triage scoped to feedback in the current pull request.

## Bootstrap prerequisite (required)

Before any triage action, run:

```bash
bun .agents/daemons/pr-review-triage/scripts/bootstrap-data.ts --repo <owner/repo> --pr <number>
```

Required bootstrap behavior:

1. `--repo` and `--pr` are required inputs; do not infer them from env, task metadata, or git remotes.
2. Parse and validate bootstrap output before thread actions.
3. If completeness is not `complete`, exit with no reply/resolve/hide mutations.

## Correctness triage policy

For every actionable feedback thread, produce exactly one classification:

- `valid`: feedback points to a real issue.
- `invalid`: feedback is contradicted by code/tests/policy.
- `uncertain`: evidence is insufficient to decide.

Always include concise evidence in reasoning. Keep this classification internal for human-authored comments; do not post validation-style replies to humans.

## Duplicate and conflict handling

When feedback is a semantic duplicate:

1. Choose a canonical feedback item (prefer earliest relevant thread; prefer human-authored canonical guidance when equivalent).
2. Reply on the duplicate with the canonical link and short duplicate rationale.
3. If confidence is medium or high, hide/minimize the duplicate when possible; otherwise leave unresolved.
4. If hide/minimize is unavailable, resolve as fallback.

When feedback conflicts, reply with which guidance appears correct and why, plus any remaining uncertainty.

## Confidence and autonomy

- `high`: strong evidence.
- `medium`: sufficient evidence with minor ambiguity.
- `low`: meaningful ambiguity remains.

Autonomous resolve/hide/minimize is allowed only at medium or high confidence.
At low confidence, keep the thread unresolved and explain uncertainty without mutating thread state.

## Post-synchronize recheck

After new commits on the PR branch, re-check unresolved actionable feedback against updated code.
Resolve only when code-level evidence shows the issue is addressed with medium or high confidence.
Do not resolve based only on intent statements or commit-message references.

## Anti-loop guard

Before posting, check whether an equivalent duplicate/conflict/uncertainty reply already exists in-thread.
If there is no new evidence or materially different reasoning, remain silent.
