# Pull Request Workflow

## When to Use This Skill

Any time you:

- Open a new pull request against `realsenseai/librealsense`
- Push new commits to an existing pull request
- Respond to inline review comments

## Pull Request Description Format

Every PR description **must** start with a TL;DR — 1–2 sentences summarising the main goal of the PR — followed by the full description below it.

```markdown
**TL;DR:** <one-to-two sentences stating the user-visible change and why>

## Summary
- <commit-or-area-level bullets explaining what changed and why>

## Why
<the bug, regression, or capability gap being addressed; link to upstream
context (issues, prior PRs) if relevant>

## Test plan
- [ ] <unit/pytest entries added or exercised, including marker / context / iteration counts>
- [ ] <manual or CI verification steps>
- [ ] <out-of-scope follow-ups, if any>
```

Notes:
- Keep the TL;DR free of internal jargon — reviewers should be able to grasp the PR's purpose in one read.
- Tables (behavior change, latency impact, benchmark results) belong **inside** the body, never inside the TL;DR.
- Reference companion or follow-up PRs by number, not URL.

## Before Every Push — Description Audit

The PR description is the **second** thing a reviewer reads (after the diff).
A description that says "20 iterations nightly" while the diff sets 5 wastes
the reviewer's time and erodes trust. So:

**Before `git push` on any PR branch, re-read the PR description and ask:**

1. Do the bullet points still match the commits actually on the branch?
2. Are any concrete numbers in the description still correct (iteration counts, timeouts, file paths, marker lists, percentages)?
3. Has the behavior change table or test-plan section drifted because of a follow-up commit (rename, refactor, scope change)?
4. Did review feedback change the design enough that the "Why" or "Behavior change" sections need an update?
5. Are referenced files / commits / tests still at the paths shown?

If any answer is "no, it's stale" → update the description **in the same
push** (via `gh pr edit <num> --body ...`). Do not let the diff and the
description diverge.

## Responding to Review Comments

- **One reply per thread.** Don't summarise multiple threads in a single
  comment — reviewers can't tell which thread is resolved.
- Reference the commit SHA that addresses the comment (`✅ Fixed in
  <sha>. <one-line summary>`).
- For deferred items, write `⏸ Deferred — <reason>` so the reviewer knows
  it's acknowledged, not lost.
- For disagreements, explain the trade-off concretely (worked example,
  edge case, perf number) before declining. Don't just say "intentional".
- **Do not auto-resolve threads** unless explicitly told to. Let the
  reviewer decide when their concern is settled.

## Handling Automated Review Bots

| Bot | How to respond |
|---|---|
| **Aikido** (`aikido-pr-checks[bot]`) | If the issue is real, fix and reply with the commit SHA. If the suggestion is wrong or intentional, reply `@AikidoSec ignore: <reason>` — the reason becomes part of the audit trail. |
| **rs-agentic-bot** (posts as a human teammate) | Treat as a real reviewer: fix or defer; reply per thread. |
| **Copilot suggestions** | Apply only if they preserve intent; reply with rationale if declined. |

## Opening a New PR via `gh`

```bash
gh pr create \
  --base development \
  --head Nir-Az:<branch> \
  --title "<short title under 70 chars>" \
  --body "$(cat <<'EOF'
**TL;DR:** <1-2 sentences>

## Summary
- ...

## Why
...

## Test plan
- [ ] ...
EOF
)"
```

- **Title**: short, imperative, under 70 chars. The body carries the
  detail, not the title.
- **Base**: always `development` (not `master`).
- **Head**: `Nir-Az:<branch>` (the fork remote).
- After creation, immediately verify the description renders correctly
  (`gh pr view <num>`).

## Quick Checklist Before Pushing

- [ ] TL;DR present and current
- [ ] Concrete numbers (iterations, timeouts, file paths) match the diff
- [ ] Test-plan checkboxes reflect what's actually exercised
- [ ] No broken links to renamed / moved files
- [ ] Companion-PR cross-references still valid
