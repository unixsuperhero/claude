# PR Blitz — Queue Agent Parties for All Failing PRs

Queue an `/agent-party` fix job for every open PR that has failing or pending checks.

## Arguments

`$ARGUMENTS` (optional): deadline string, e.g. `"EOD 2026-03-18"`. Defaults to `"EOD [today's date]"`.

## Steps

### Step 1 — Gather context (run in parallel)

Run all of the following simultaneously:

```bash
h pr update
```

```bash
h task ls
```

```bash
ls ~/.claude/project-manager/
```

Then, for each project found in `~/.claude/project-manager/`, read its PROJECT.md:

```bash
cat ~/.claude/project-manager/PROJECT_SLUG/PROJECT.md
```

Also list the claude-docs directory for reference:

```bash
ls ~/notes/claude-docs/
```

### Step 2 — Project status

Run the `/project-status` skill to generate a full status report. Display it to the user.

### Step 3 — Parse PRs and match to tasks

From the `h pr update` output, collect all open PRs. The format is:

```
N. #PRNUM [o STATUS  X/ Y] -a/-cr BRANCH_NAME
   PR Title
   https://github.com/instacart/carrot/pull/PRNUM
```

Status icons:
- `✅` = all checks passed — **skip** (nothing to fix)
- `❌` = checks failing — **queue a fix**
- `⏳` = checks pending — **queue a fix** (likely stale, needs rebase)
- `[d ...]` = draft PR — **skip** unless it also has `❌`

From the `h task ls` output, build a map of `branch-name → task short-name`. The format is:

```
   TASK_NAME   WORKTREE_PATH   [branch-name]   (hiiro-path)
```

Example:
```
*@ saform   saform/main   [sa-form-regex-validations]   (saform)
```
→ branch `sa-form-regex-validations` maps to task `saform`

For child tasks (indented with `-`), use the child task name, e.g.:
```
   - keyword   saform/keyword   [sa-keyword-attribute-pattern-validation]   (saform/keyword)
```
→ task name is `saform/keyword`

For each PR needing a fix, determine:
1. **Branch name** — from the PR line (the word after `-a/-cr`)
2. **Task name** — from the branch→task map above
3. **Notes file** — derive from the branch name: take the branch name, replace it with a reasonable slug, e.g.:
   - `sa-form-regex-validations` → `saform-regex-notes.md`
   - `sa-keyword-attribute-pattern-validation` → `saform-keyword-notes.md`
   - `cutover-t4-monitors-frontend` → `cutover-task4-monitors.md`
   - `cutover-t3-storefront-schema` → `cutover-task3-admin-banner.md`
   - When in doubt, use `TASKNAME.md` where TASKNAME is the hiiro task short name
4. **Deadline** — use `$ARGUMENTS` if provided, else `"EOD [today's date]"`
5. **Project-manager context** — search the loaded PROJECT.md files for a row where the Branch column matches the branch name. Extract the task name, status, priority, and any notes from that row.
6. **Claude-docs context** — if the notes file exists at `~/notes/claude-docs/NOTES_FILE`, read the last 30 lines for recent progress context.

### Step 4 — Queue agent parties

For each PR needing a fix where a matching task was found, run this bash command:

```bash
h task queue add -t TASK_NAME -n "pr-blitz-PRNUM" << 'PROMPT'
/agent-party with agents: git-coordinator, worktree-expert, hiiro-expert, task-project-manager, partners-expert, lint-specs-expert, endpoint-expert, store-config-expert, tooling-advisor

/fix-pr PR_URL

Fix all failing checks on the BRANCH_NAME PR.
Push. Mark ready-for-review when clean.
Update ~/notes/claude-docs/NOTES_FILE with progress.
Deadline: DEADLINE.

## Project context (from project-manager)
PROJECT_MANAGER_CONTEXT

## Recent progress (from claude-docs)
CLAUDE_DOCS_CONTEXT
PROMPT
```

Substitute:
- `TASK_NAME` — hiiro task name (e.g. `saform`, `saform/keyword`, `cutover/monitors`)
- `PRNUM` — PR number (e.g. `746330`)
- `PR_URL` — full GitHub URL (e.g. `https://github.com/instacart/carrot/pull/746330`)
- `BRANCH_NAME` — git branch name (e.g. `sa-form-regex-validations`)
- `NOTES_FILE` — derived notes filename (e.g. `saform-regex-notes.md`)
- `DEADLINE` — from `$ARGUMENTS` or today's EOD
- `PROJECT_MANAGER_CONTEXT` — the matching task row + notes from the PROJECT.md (status, priority, any task-level notes). If no match found, write "No project-manager entry found."
- `CLAUDE_DOCS_CONTEXT` — last 30 lines of `~/notes/claude-docs/NOTES_FILE` if the file exists; otherwise "No prior notes found."

If the PR has extra context (e.g. it's a multi-PR task like cutover t4 with both partners and frontend), include that in the prompt body — e.g. "This is the frontend PR; the partners PR #NNNN should be handled separately in its own task."

### Step 5 — Update claude-docs logs

After queuing, for each PR that was queued, append a log entry to `~/notes/claude-docs/NOTES_FILE`:

```
## YYYY-MM-DD HH:MM
- pr-blitz queued agent-party for PR #PRNUM (BRANCH_NAME)
- Checks status: STATUS (❌ failing / ⏳ pending)
- Deadline: DEADLINE
- Queue job name: pr-blitz-PRNUM
```

If the notes file does not yet exist, create it with a header:

```
# TASK_NAME — PR #PRNUM

## Branch: `BRANCH_NAME`
## PR: PR_URL

---

## YYYY-MM-DD HH:MM
- pr-blitz queued agent-party for PR #PRNUM (BRANCH_NAME)
- Checks status: STATUS
- Deadline: DEADLINE
- Queue job name: pr-blitz-PRNUM
```

### Step 6 — Handle unmatched PRs

If a PR has no matching task in `h task ls` (branch not found in any task), do NOT queue anything. Instead, report it to the user: "PR #NNNN (branch: BRANCH) has no matching hiiro task — manual attention needed."

### Step 7 — Report to user

Output a summary table:

```
PR     | Branch                        | Task            | PM Status    | Action
-------|-------------------------------|-----------------|--------------|------------------
#74630 | sa-form-regex-validations     | saform          | inprogress   | Queued
#74634 | sa-keyword-attribute-...      | saform/keyword  | inprogress   | Queued
#74775 | cutover-t4-monitors-frontend  | cutover/monitors| complete     | Queued
#73813 | aldi-add-nav-sidebar-links    | ???             | --           | No task — manual
```

Then:
- Show the full `/project-status` output
- Print: "Queued N agent parties. Check status with `h queue ls`."
