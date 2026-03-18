---
description: Set up the correct environment (worktree, hiiro task, branch, latest changes) before making changes to a PR
---

# /change-pr

Use `/agent-party` for coordination. Before making any changes, establish the correct environment in priority order.

## Step 1 — Worktree and hiiro task (highest priority)

Use the **worktree-expert** and **hiiro-expert** agents for this step.

Find the correct hiiro task and git worktree for this PR's branch:

```bash
h task ls
h wt ls
```

If a worktree already exists for this branch or task, switch into it. Do not create a new one if one already exists.

If no worktree exists for this task, check available disk space:

```bash
df -h ~
```

Only if there is sufficient disk space, create a subtask worktree using sparse checkout:

```bash
h subtask start SUBTASK_NAME -s default
```

Use the `default` sparse checkout group unless a more specific group is appropriate for the files being changed.

There may be a general subtask used for all of the parent task's subtasks — check for that first before creating a new one.

## Step 2 — Branch

Once inside the correct worktree, verify the active branch matches the PR's branch:

```bash
git branch --show-current
```

If not on the correct branch, switch to it:

```bash
git checkout BRANCH_NAME
```

Do not create a new branch. The branch for this PR must already exist.

## Step 3 — Sync latest changes

Use the **git-coordinator** agent for this step.

Check whether the remote branch has commits not present locally (this commonly happens after using GitHub's "Update Branch" feature, which merges or rebases off of main):

```bash
git fetch origin BRANCH_NAME
git log HEAD..origin/BRANCH_NAME --oneline
```

If the remote is ahead, pull the latest:

```bash
git pull origin BRANCH_NAME
```

Do not force-push or reset. Only fast-forward pulls are safe here.

---

## Then — do what the user is asking

With the environment verified, proceed with the user's requested changes.

$ARGUMENTS
