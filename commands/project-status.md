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

## Context Detection

**Before Step 1**, determine whether this command is running in a session that already has project context loaded (tasks, PRs, work logs already read earlier in the conversation):

- **Active session** (tasks, PRs, and work logs already in context):
  1. Skip re-reading files — use the data already in context
  2. Run only the PR refresh command (Step 1, abbreviated below)
  3. Generate a fresh report superseding the previous one
  4. Proceed directly to Step 7

- **Fresh session** (no prior context): run the full workflow from Step 1 through Step 7.

In either case, **always** refresh PR statuses — never report on stale data.

---

## Step 1: Refresh PR Statuses

Run both in parallel:

```bash
h pr ls -u
h task ls
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
| Pending deploys | N |
| Docs/comms needed | N |

---

## Next Steps

A dependency-ordered flat list of **all actions needed right now**, across all projects.

Include **every category** of next step — not just PRs and code:
- Deployments and rollouts
- Documentation updates (runbooks, Confluence, READMEs)
- Stakeholder / team communication (Slack announcements, Jira updates)
- Monitoring, alerting, or validation steps after merges
- Follow-up tasks or tickets to create
- Cleanup (prune stale branches/PRs, remove feature flags)
- Any blockers that need resolution before work can continue

Rules for ordering:
- Independent/easy actions come first (things that can be done immediately)
- If action B depends on action A completing first, B must come after A
- Within the same priority level: failing PRs > deploys > merges > reviews > docs/comms

1. **[Action verb] [PR/task reference as markdown link]** — [one-line reason]
   - **Shell:** `h task queue add "/fix-pr"`
2. **Merge [PR #NNNN — Title](url)** (`project-name`) — approved, all checks green
   - **Shell:** `h pr merge NNNN`
3. [continue for all actionable items in execution order, including non-code steps]

---

## Projects

### [Project Name]

> **Goal:** [from work log if available, otherwise infer from task name and PR titles]

**Tasks:** `task-name`, `task-name/subtask1`, ...
**Status:** [one-line summary of where this project stands]

#### PRs

| Status | PR | Title |
|--------|----|-------|
| 🔴 FAILING | [#NNNN](url) | [PR Title](#1-status-badge-nnnn--pr-title) |
| 🟢 APPROVED | [#MMMM](url) | [PR Title](#2-status-badge-mmmm--pr-title) |

[one row per PR in merge order; Title cell is an anchor link to the PR's heading below]

#### PRs (merge order)

##### 1. [STATUS BADGE] [#NNNN — PR Title](https://github.com/...)
- **Branch:** `branch-name`
- **Worktree:** `~/work/task/main`
- **Checks:** N/N passing [or: N failing, N pending]
- **Reviews:** [N approved / changes requested / REVIEW_REQUIRED]
- **Draft:** yes/no

**Next Steps:**
- [ ] [specific actionable next step — fix, review, or merge action]
- [ ] [any post-merge step: deploy, flag cleanup, monitoring, docs, comms]

**Prompts to run:**

1. **Switch to task context** — Shell command
   ```
   h task switch [task-name]
   ```
2. **Fix failing checks** — Claude prompt
   ```
   h task queue add "/fix-pr"
   ```

[only include if checks are failing; omit the task-switch step if already on the right task]

---

[repeat for each PR in merge order]

#### Project Next Steps

Go beyond PRs — include every kind of action needed to complete this project:

- [ ] [PR/code action if applicable]
- [ ] [deployment or rollout step if applicable]
- [ ] [documentation update if applicable — runbook, Confluence, README]
- [ ] [stakeholder communication if applicable — Slack, Jira, email]
- [ ] [monitoring or validation step after deploy]
- [ ] [follow-up tasks or tickets to create]
- [ ] [cleanup — feature flags, stale branches, etc.]

Only include items that are actually relevant to this project based on work logs and PR context. Do not fabricate steps.

---

[repeat for each project]

---

## Prompts to Run

A copy-paste ready list of all actions you should run, as labeled steps:

### Fix Failing PRs

[For each FAILING PR:]

1. **Fix [PR #NNNN — title](url)** — Claude prompt
   ```
   h task queue add "/fix-pr"
   ```

### PRs Ready to Merge

[For each APPROVED PR:]

1. **Merge [PR #NNNN — title](url)** — Shell command
   ```
   h pr merge NNNN
   ```

### PRs Needing Review

[For each NEEDS_REVIEW PR:]

1. **Request review on [PR #NNNN — title](url)** — Shell command
   ```
   h pr ready NNNN
   ```

---

## Stale / Merged PRs

[List any merged or closed PRs still tracked — these can be pruned with `h pr prune`]

1. **Prune stale PRs** — Shell command
   ```
   h pr prune
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

**If `mdoc` fails or is unavailable**, generate a fallback HTML error report instead:

1. Write an HTML file to `~/claude/docs/project-status-error-YYYY-MM-DD-HHMMSS.html` containing:
   - A clear error banner explaining mdoc failed
   - The **original user request** that triggered this `/project-status` run (copy it verbatim from conversation context)
   - The raw markdown report content (in a `<pre>` block), so the data is not lost
   - The error output from mdoc if available
   - Timestamp

2. Append the file path to `~/claude/index.json` (or update it if you can, same format as other entries)

3. Open the file:
   ```bash
   open ~/claude/docs/project-status-error-YYYY-MM-DD-HHMMSS.html
   ```

---

## Handling Missing Data

- **No pinned PRs**: report "No PRs tracked. Run `h pr track` on your branches."
- **No tasks**: report "No tasks found in tasks.yml."
- **No work logs**: skip the goal/context line for that task — don't fabricate it.
- **PR has no task field**: group under "Unassigned PRs" section at bottom of report.
- **`h pr ls -u` fails**: continue with cached data from pinned_prs.yml, note the refresh failed.

---

## Key Rules

- Never invent task goals or next steps — only include what's in work logs or directly inferable from PR titles/check names.
- Always show the actual check names that are failing, not just "N checks failed".
- The prompts section must be copy-paste ready — use `h task queue add "/fix-pr"` for Claude prompts and `h pr merge NNNN` for shell commands. Label each step clearly as "Shell command" or "Claude prompt".
- Merge order is a suggestion, not a strict dependency graph — mark it clearly as "suggested order".
- ALWAYS include a blank link between markdown element types when generating
  markdown.   Meaning, a blank line between a paragraph and a bulleted list.  a
  blank line between a head and a paragraph, etc.
- ALWAYS render PR references as markdown links `[#NNNN — Title](url)` — never
  as bare URLs or plain `#NNNN` text. The URL comes from the `url` field in
  pinned_prs.yml. This applies everywhere: PR headings, roadmap list items,
  prompts sections, and any inline mention of a PR.
