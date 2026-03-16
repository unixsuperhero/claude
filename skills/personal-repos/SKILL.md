---
name: personal-repos
description: Use when working in ~/proj/claude/ or ~/proj/home/, editing dotfiles, Claude settings, CLAUDE.md, skills, plugins, commands, hooks, or any personal configuration files. Activates when the user is maintaining their home dotfiles repo or their Claude config/tools repo.
version: 1.0.0
---

# Personal Repos: Claude Config & Dotfiles

This skill provides context and agent guidance for maintaining two personal repos:

- `~/proj/claude/` — Claude Code config, skills, plugins, commands, hooks, CLAUDE.md
- `~/proj/home/` — Home dotfiles: shell config, tool configs, bin scripts, Brewfile, etc.

The `~/.claude/` directory is kept in sync with `~/proj/claude/` via symlinks.
The `~/` dotfiles are kept in sync with `~/proj/home/` via symlinks or direct files.

## Agents

Three agent roles handle maintenance tasks on these repos. Dispatch them via Hiiro teams
(`h team create` / `h team send`) or as standalone agents in a `SendMessage` call.

### `claude-settings-sync`

**Purpose:** Sync `~/.claude/` changes into the `~/proj/claude/` git repo, then commit and push.

**Responsibilities:**
- Find files in `~/.claude/` that are not yet symlinked to `~/proj/claude/`
- Move untracked files to `~/proj/claude/` and create symlinks back
- `cd ~/proj/claude && git add -A && git commit -m "..." && git push`

**When to invoke:**
- After creating or editing a skill, plugin, command, hook, or agent in `~/.claude/`
- After updating `~/CLAUDE.md` or any Claude settings
- Whenever `~/proj/claude/` should be brought up to date with live `~/.claude/` state

---

### `dotfiles-sync`

**Purpose:** Commit and push dotfile changes in `~/proj/home/`.

**Responsibilities:**
- `cd ~/proj/home && git status` to see what changed
- Stage relevant changes and commit with a descriptive message
- Push to remote

**When to invoke:**
- After editing shell config (`.zprofile`, `.zshrc`, etc.), tool configs, bin scripts,
  Brewfile, or any file tracked in `~/proj/home/`
- After making changes to configs under `~/proj/home/.config/`
- Whenever `~/proj/home/` has uncommitted changes that should be preserved

---

### `task-project-manager`

**Purpose:** Log work progress and manage Hiiro task state.

**Responsibilities:**
- Check `h task ls` for the active task context
- Create or append to a log file in `~/notes/claude-docs/` (e.g. `dotfiles-sync.md`)
- Use the log entry format: `## YYYY-MM-DD HH:MM` followed by bullet points
- Update task status via `TaskUpdate` (in_progress / completed)

**When to invoke:**
- At the end of a work session when progress should be logged
- When starting a task that needs hiiro context surfaced
- As a closing step in any multi-step workflow to record what was done

---

## Typical Workflow

When editing Claude config (skills, plugins, CLAUDE.md, etc.):
1. Make changes in `~/.claude/` or directly in `~/proj/claude/`
2. Dispatch **`claude-settings-sync`** to commit and push
3. Dispatch **`task-project-manager`** to log the work

When editing dotfiles (shell, tool configs, bin scripts, etc.):
1. Make changes under `~/proj/home/`
2. Dispatch **`dotfiles-sync`** to commit and push
3. Dispatch **`task-project-manager`** to log the work

When both repos are touched in the same session, run both sync agents (they are
independent and can run in parallel), then run `task-project-manager` last.

## Repo Paths Reference

| Location | Repo | Notes |
|---|---|---|
| `~/.claude/` | `~/proj/claude/` | Synced via symlinks |
| `~/CLAUDE.md` | `~/proj/claude/` | Global Claude instructions |
| `~/.claude/skills/` | `~/proj/claude/` | Custom skills |
| `~/.claude/plugins/` | `~/proj/claude/` | Installed plugins |
| `~/proj/home/.config/` | `~/proj/home/` | Tool configs (ghostty, helix, nvim, etc.) |
| `~/proj/home/bin/` | `~/proj/home/` | Custom bin scripts |
| `~/proj/home/Brewfile` | `~/proj/home/` | Homebrew package list |
