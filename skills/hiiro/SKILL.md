---
name: hiiro
description: >
  Reference for the Hiiro CLI framework — task/worktree management, the Claude
  prompt queue, and PR tracking. Use when the user asks about `h task`, `h subtask`,
  `h queue`, `h pr`, or any Hiiro subcommand; when looking up task context, branch,
  session, or worktree for the current environment; or when spinning up a new Claude
  Code session via the queue.
---

# Hiiro

> **For complex hiiro operations** (worktree management, task isolation, ensuring changes are in the correct worktree), use the `hiiro-expert` agent via the Agent tool with `subagent_type: 'hiiro-expert'`.

Hiiro is a Ruby CLI framework installed as a gem. All commands start with `h`.
Config lives in `~/.config/hiiro/`. Tasks, queues, and PRs are the three core
concepts you'll interact with daily.

---

## 1. Tasks & Subtasks

### Concept

A **task** is a named unit of work that ties together three things:

| Resource      | Description                                 |
|---------------|---------------------------------------------|
| **Name**      | Human-readable identifier, e.g. `my-feature` |
| **Worktree**  | A git worktree path, e.g. `~/work/my-feature/main` |
| **Tmux session** | A tmux session with the same name as the task |

When you `h task start my-feature`, Hiiro:
1. Creates (or reuses) a git worktree at `~/work/my-feature/main`
2. Saves the task record to `~/.config/hiiro/tasks/tasks.yml`
3. Creates a tmux session named `my-feature` and switches to it

**Subtasks** follow the same pattern but are children of a top-level task.
A subtask named `auth` under `my-feature` gets:
- Name: `my-feature/auth`
- Worktree: `~/work/my-feature/auth`
- Tmux session: `my-feature/auth`

### Config files

```
~/.config/hiiro/tasks/tasks.yml   # All task records
~/.config/hiiro/apps.yml          # App directory mappings (relative to worktree root)
```

`tasks.yml` structure:
```yaml
tasks:
  - name: my-feature
    tree: my-feature/main          # worktree name relative to ~/work/
    session: my-feature            # tmux session name (defaults to name)
  - name: my-feature/auth
    tree: my-feature/auth
    session: my-feature/auth
```

### Task commands (`h task COMMAND`)

```bash
h task list                     # List all tasks with worktree, branch, session
h task ls                       # Alias for list

h task start NAME               # Create or switch to a task (creates worktree + tmux session)
h task start NAME APP           # Start in a specific app subdirectory
h task start NAME -s GROUP      # Start with sparse checkout (repeatable)

h task switch NAME              # Switch to an existing task's tmux session
h task switch NAME -f           # Force switch even if session is already attached
h task switch                   # Interactive fuzzy select from all tasks

h task stop NAME                # Remove task record (worktree stays, becomes available)

h task status                   # Show current task, worktree, path, session
h task st                       # Alias for status

h task current                  # Print current task name (useful in scripts)
h task cbranch                  # Print current task's branch
h task ctree                    # Print current task's worktree name
h task csession                 # Print current task's tmux session name

h task branch NAME              # Print task's git branch (fuzzy select if no name)
h task tree NAME                # Print task's worktree name
h task session NAME             # Print task's tmux session name

h task cd APP                   # cd to app directory within current task's worktree
h task path APP                 # Print path to app directory
h task app APP                  # Open app in a new tmux window
h task apps                     # List configured apps

h task todo ls                  # List todos for current task
h task todo add TEXT            # Add a todo item
h task todo done INDEX          # Mark todo done
```

### Subtask commands (`h subtask COMMAND`)

Subtask commands are identical to task commands but scoped to children of the
current top-level task:

```bash
h subtask list
h subtask start NAME
h subtask switch NAME
h subtask stop NAME
h subtask status
```

### Looking up task info from code/scripts

```bash
h task branch my-feature        # → main or feature-branch-name
h task session my-feature       # → my-feature
h task tree my-feature          # → my-feature/main
h task path                     # → /Users/josh/work/my-feature/main  (current task root)
h task path rails               # → /Users/josh/work/my-feature/main/rails
```

---

## 2. Queue (`h queue COMMAND`)

The queue lets you write Claude Code prompts as markdown files and run them
asynchronously in tmux windows.

### Concept

Prompts flow through statuses: `wip` → `pending` → `running` → `done`/`failed`

```
~/.config/hiiro/data/queue/
  wip/        ← drafts, not yet ready to run
  pending/    ← ready to launch
  running/    ← currently running (has .meta sidecar with tmux info)
  done/       ← completed successfully
  failed/     ← exited non-zero
```

Each task is a `.md` file named after a slug of the prompt content. An optional
YAML frontmatter block pins the task to a specific worktree/session:

```markdown
---
task_name: my-feature
tree_name: my-feature/main
session_name: my-feature
---

Implement the user authentication flow described in docs/auth-spec.md.
Focus on the OAuth2 callback handler in app/controllers/auth_controller.rb.
```

When launched, Hiiro:
1. Moves the file from `pending/` to `running/`
2. Opens a new tmux window in the task's tmux session (or `hq` default)
3. Runs `cat prompt | claude` in the task's worktree directory
4. Moves the file to `done/` or `failed/` based on exit code

### Queue commands

```bash
h queue ls                      # List all tasks by status with timestamps and preview
h queue ls -a                   # Show all (no 10-item limit per status)
h queue status                  # Detailed status with session/window/dir info

h queue add                     # Open editor to write a new prompt → goes to pending
h queue add -t TASK             # Associate with a specific task
h queue add -T                  # Interactively choose task
h queue add "inline prompt"     # Quick add from command line
cat prompt.md | h queue add     # Add from stdin

h queue wip NAME                # Create/edit a wip draft by name
h queue ready                   # Move wip task to pending (fuzzy select if multiple)
h queue ready NAME              # Move specific wip task to pending

h queue run                     # Launch all pending tasks now
h queue run NAME                # Launch a specific pending task
h queue watch                   # Continuously poll pending/ and launch (runs as daemon)

h queue attach                  # Fuzzy select running task and switch to its tmux window
h queue attach NAME             # Switch to specific running task's window

h queue kill                    # Kill running task (moves to failed)
h queue kill NAME               # Kill specific task

h queue retry                   # Move failed/done task back to pending
h queue retry NAME              # Retry specific task

h queue clean                   # Remove all done/failed files
h queue dir                     # Print queue directory path
```

### Spinning up a new Claude Code session via queue

This is the primary way to delegate work to Claude Code in a different worktree:

```bash
# From within any task session:
h queue add -t my-other-feature

# Or use the context-aware version from inside a task command:
h task queue add   # pre-fills frontmatter with current task info
```

The queue `watch` daemon is typically run in the `hq` tmux session:
```bash
h queue session    # Switch to / create the hq session
h queue watch      # Start the watcher in that session
```

---

## 3. PR Tracking (`h pr COMMAND`)

PRs are tracked locally in `~/.config/hiiro/pinned_prs.yml`. The file stores
PR metadata including the associated task, worktree, and tmux session captured
at track time.

### Config file

```
~/.config/hiiro/pinned_prs.yml
```

Structure:
```yaml
- number: 1234
  title: "Add OAuth2 callback handler"
  url: "https://github.com/org/repo/pull/1234"
  headRefName: "my-feature-branch"
  state: OPEN
  is_draft: false
  task: my-feature              # ← captured from task context at track time
  worktree: my-feature/main     # ← captured from task context
  tmux_session: my-feature      # ← captured from task context
  slot: 1                       # ← stable position number for reference
  checks:
    total: 42
    success: 40
    pending: 2
    failed: 0
  reviews:
    approved: 1
    changes_requested: 0
    commented: 0
    reviewers:
      alice: APPROVED
  last_checked: "2026-03-12T10:00:00Z"
  pinned_at: "2026-03-10T09:00:00Z"
```

### Tracking PRs

```bash
h pr track                      # Track current branch's PR (auto-detects from git)
h pr track 1234                 # Track PR by number
h pr track -                    # Track current branch's PR explicitly

# At track time, Hiiro captures the current task/worktree/session context
# and stores it in pinned_prs.yml alongside the PR metadata.
```

### Listing and status

```bash
h pr ls                         # List all tracked PRs (compact, one line each)
h pr ls -u                      # List + refresh status from GitHub first

h pr status                     # Detailed view: checks, reviews, branch, URL for each PR

h pr update                     # Refresh all tracked PR statuses from GitHub
h pr update -U                  # Force refresh even if recently checked (within 2 min)
```

Example `h pr ls` output:
```
  1. [O ✅] #1234 Add OAuth2 callback  checks:40/42 | 1 approved
  2. [O ⏳] #1235 Refactor auth module checks:12/42
  3. [D]    #1236 WIP: new payment flow
```

State codes: `O`=open, `D`=draft, `M`=merged, `X`=closed
Check icons: `✅`=all passing, `⏳`=pending, `❌`=failing, `⏳❌`=both

### Getting PR info

```bash
h pr view 1234                  # Show PR details via gh
h pr view                       # Fuzzy select from tracked PRs

h pr link 1234                  # Print PR URL
h pr link                       # Fuzzy select → print URL

# Slot numbers let you reference PRs by position:
h pr view 1                     # View the PR in slot 1
h pr open 2                     # Open PR #2 (by slot) in browser
```

### PR actions

```bash
h pr open 1234                  # Open PR in browser
h pr checkout 1234              # gh pr checkout
h pr diff 1234                  # gh pr diff
h pr merge 1234                 # gh pr merge
h pr ready 1234                 # Mark PR as ready for review
h pr to-draft 1234              # Convert back to draft
h pr comment 1234               # Open editor to write a comment

h pr check 1234                 # Run gh pr checks (one-shot)
h pr watch 1234                 # Watch checks until completion (notifies on done)
h pr fwatch 1234                # Watch with --fail-fast

h pr attach 1234                # Open a new tmux window in the PR's task session,
                                # checking out the PR branch (commits WIP first if dirty)
```

### Filtering tracked PRs

```bash
h pr green                      # PRs with all checks passing
h pr red                        # PRs with failing checks
h pr draft                      # Draft PRs
h pr old                        # Merged PRs

h pr created                    # All open PRs authored by you (from GitHub)
h pr assigned                   # All open PRs assigned to you (from GitHub)
h pr missing                    # Your PRs not yet tracked
h pr amissing                   # Interactive: add missing PRs to tracking

h pr for-task NAME              # PRs associated with a specific task
h pr for-task                   # PRs for the current task (auto-detected)

h pr prune                      # Remove merged/closed PRs from tracking
h pr rm 1234                    # Remove a specific PR from tracking
```

### PR comment templates

```bash
h pr templates                  # List saved templates
h pr new-template NAME          # Create a new template (opens editor)
h pr from-template 1234         # Post a template comment on a PR (fuzzy select template)
```

Templates are stored in `~/.config/hiiro/pr_templates/*.md`.

---

## Quick Reference

### "What task am I in?"
```bash
h task status         # Full info: name, worktree, path, session
h task current        # Just the name
```

### "What branch is my-feature on?"
```bash
h task branch my-feature
```

### "Start a new Claude session on my task"
```bash
h queue add -t my-feature      # Write prompt → appears in pending → auto-launched by watcher
# or if already in the task session:
h task queue add               # Pre-fills frontmatter with current task
```

### "Which PRs need attention?"
```bash
h pr update && h pr ls         # Refresh then list
h pr red                       # Show failing PRs
h pr status                    # Detailed view with reviewer info
```

### "Get branch name for a PR"
```bash
# From pinned_prs.yml — the headRefName field
h pr ls                        # Shows branch in detailed view
h pr view 1234                 # Shows headRefName
```

### "Jump to a PR's working session"
```bash
h pr attach 1234               # Opens new window in the task's tmux session on the PR branch
```

---

## Abbreviation Matching

All Hiiro commands support prefix abbreviation. You can type the shortest
unambiguous prefix:

```bash
h t st          # → h task status
h t sw          # → h task switch
h q ls          # → h queue ls
h pr tr         # → h pr track
h pr upd        # → h pr update
```

# RULES

ANYTIME YOU `h task start` or `h subtask start` always use sparse checkout
the group you should probably use is `default` so

`h task start TASKNAME -s default`
