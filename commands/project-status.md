---
description: Full project status report — tasks, PRs grouped by project in merge order, next steps, and fix prompts. Generates HTML via mdoc and opens in browser.
---

# /project-status

Generate a comprehensive project status report across all tasks and tracked PRs.

## Overview

This command:
1. Refreshes all PR statuses from GitHub
2. Gathers all tasks and their relationships
3. Reads work logs for context on each task
4. Produces a markdown report grouped by project, PRs in merge order
5. Give reports in the context of the project and what is left to do, not just
   the git/pr aspect.  look in the relevant docs in ~/notes/claude-docs/
6. Converts to HTML via `mdoc` and opens in browser

---

## Step 1: Refresh PR Statuses

Run both in parallel:

```bash
h pr update -U
h task ls
```

Then:

```bash
h pr ls
```

---

## Step 2: Read Data Sources

Read all of these in parallel:

- `~/.config/hiiro/pinned_prs.yml` — full PR metadata including checks, reviews, task associations
- `~/.config/hiiro/tasks/tasks.yml` — all tasks and their worktrees
- All files under `~/notes/claude-docs/` — work logs (use Glob then Read in parallel)

Parse the YAML files to build a complete picture of each task and its associated PRs.

---

## Step 3: Build Project Groups

Group tasks into projects by their top-level name:

- `cutover` owns: `cutover`, `cutover/shutdown-date`, `cutover/banner`, `cutover/monitors`, `cutover/parmonitors`
- `oncall` owns: `oncall`, `oncall/posoi`, `oncall/propagation`
- `saform` owns: `saform`, `saform/keyword`
- Top-level tasks with no subtasks are their own project

For each group, gather:
- All subtask names and worktrees
- All PRs associated with the task (use `task` field in pinned_prs.yml)
- Latest work log entries from `~/notes/claude-docs/`

---

## Step 4: Determine PR Merge Order

Within each project, order PRs for merging:

1. **Base PRs first** — PRs whose branch other PRs are likely based on (check `headRefName` patterns)
2. **Passing checks before pending** — green PRs can merge now
3. **Approved before needs-review** — approved PRs are closer to done
4. **Non-draft before draft** — ready PRs come before WIP

Use this heuristic: if PR A's branch name is a fix-pr of PR B's branch name, A should be merged first.

Mark explicit merge prerequisites in the report if detectable.

---

## Step 5: Classify Each PR

For each PR, determine its status class and next action:

| Condition | Status | Next Action |
|-----------|--------|-------------|
| `checks.failed > 0` | `FAILING` | Run `/fix-pr` |
| `checks.pending > 0` and `checks.failed == 0` | `PENDING` | Wait for CI |
| All checks success and `review_decision == REVIEW_REQUIRED` | `NEEDS_REVIEW` | Request review / mark ready |
| All checks success and `review_decision == APPROVED` | `APPROVED` | Ready to merge |
| `state == MERGED` | `MERGED` | Done |
| `is_draft == true` | `DRAFT` | Complete work, then mark ready |
| `state == CLOSED` | `CLOSED` | Closed/abandoned |

---

## Step 6: Generate Markdown Report

Write the report to `/tmp/project-status-$(date +%Y-%m-%d).md`.

### Report Structure

```markdown
# Project Status Report — YYYY-MM-DD

## Summary

| Metric | Count |
|--------|-------|
| Active tasks | N |
| Tracked PRs | N |
| Passing | N |
| Failing (need fix) | N |
| Pending CI | N |
| Awaiting review | N |
| Ready to merge | N |

---

## Projects

### [Project Name]

> **Goal:** [from work log if available, otherwise infer from task name and PR titles]

**Tasks:** `task-name`, `task-name/subtask1`, ...
**Status:** [one-line summary of where this project stands]

#### PRs (merge order)

##### 1. [STATUS BADGE] [#NNNN — PR Title](https://github.com/...)
- **Branch:** `branch-name`
- **Worktree:** `~/work/task/main`
- **Checks:** N/N passing [or: N failing, N pending]
- **Reviews:** [N approved / changes requested / REVIEW_REQUIRED]
- **Draft:** yes/no

**Next Steps:**
- [ ] [specific actionable next step]
- [ ] [next step]

**Prompts to run:**
```
/fix-pr
```
[only include if checks are failing]

---

[repeat for each PR in merge order]

#### Task Next Steps
- [ ] [overall task-level next step from work log or inferred]
- [ ] [more steps]

---

[repeat for each project]

---

## Roadmap — Ordered Actions

A prioritized flat list of the most important things to do right now, across all projects:

1. **Fix failing [PR #NNNN](https://github.com/...)** (`project-name`) — N checks failing
   > `/fix-pr` ← run this
2. **Merge [PR #NNNN](https://github.com/...)** (`project-name`) — approved, all checks green
3. **Request review on [PR #NNNN](https://github.com/...)** (`project-name`) — checks passing, needs review
4. [continue for all PRs needing attention]

---

## Prompts to Run

A copy-paste ready list of all prompts you should run:

### Fix Failing PRs

[For each FAILING PR, include the PR URL as a markdown link:]
```
# Fix [PR #NNNN: title](https://github.com/...)
h task switch [task-name]
/fix-pr
```

### PRs Ready to Merge

[For each APPROVED PR, include the PR URL as a markdown link:]
```
# Merge [PR #NNNN: title](https://github.com/...)
h pr merge NNNN
```

### PRs Needing Review

[For each NEEDS_REVIEW PR, include the PR URL as a markdown link:]
```
# Request review on [PR #NNNN: title](https://github.com/...)
h pr ready NNNN
```

---

## Stale / Merged PRs

[List any merged or closed PRs still tracked — these can be pruned with `h pr prune`]

```
h pr prune    # remove merged/closed PRs from tracking
```
```

---

## Status Badge Key

Use these badges in the report:

| Badge | Meaning |
|-------|---------|
| `🔴 FAILING` | One or more checks failing — needs fix |
| `🟡 PENDING` | CI still running |
| `🟢 APPROVED` | All checks pass, approved — merge when ready |
| `🔵 NEEDS_REVIEW` | Checks pass, awaiting reviewer |
| `⚫ DRAFT` | WIP, not ready for review |
| `✅ MERGED` | Already merged |
| `❌ CLOSED` | Closed/abandoned |

---

## Step 7: Convert and Open

After writing the report to `/tmp/project-status-YYYY-MM-DD.md`, run:

```bash
mdoc /tmp/project-status-YYYY-MM-DD.md \
  --title "Project Status — $(date +%Y-%m-%d)" \
  --desc "Tasks, PRs by project, merge order, next steps" \
  --toc
```

This generates styled HTML, updates `~/claude/index.html`, and opens the report in your browser.

---

## Handling Missing Data

- **No pinned PRs**: report "No PRs tracked. Run `h pr track` on your branches."
- **No tasks**: report "No tasks found in tasks.yml."
- **No work logs**: skip the goal/context line for that task — don't fabricate it.
- **PR has no task field**: group under "Unassigned PRs" section at bottom of report.
- **`h pr update` fails**: continue with cached data from pinned_prs.yml, note the refresh failed.

---

## Key Rules

- Never invent task goals or next steps — only include what's in work logs or directly inferable from PR titles/check names.
- Always show the actual check names that are failing, not just "N checks failed".
- The prompts section must be copy-paste ready — include the exact `h task switch` to get to the right context first.
- Merge order is a suggestion, not a strict dependency graph — mark it clearly as "suggested order".
- ALWAYS include a blank link between markdown element types when generating
  markdown.   Meaning, a blank line between a paragraph and a bulleted list.  a
  blank line between a head and a paragraph, etc.
- ALWAYS render PR references as markdown links `[#NNNN — Title](url)` — never
  as bare URLs or plain `#NNNN` text. The URL comes from the `url` field in
  pinned_prs.yml. This applies everywhere: PR headings, roadmap list items,
  prompts sections, and any inline mention of a PR.
