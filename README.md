# claude

Personal Claude Code configuration — agents, commands, skills, and settings synced from `~/.claude/`.

`~/.claude/` is kept in sync with this repo via symlinks managed by `script/setup`.

---

## Agents

Agents are specialized sub-agents invoked via the `Agent` tool. Each lives in `agents/` and declares its own tool set, model, and instructions.

| Agent | Description |
|-------|-------------|
| `ada` | Code simplification and TypeScript specialist for the isc-web monorepo. Runs after coding tasks to clean up recently changed files — removes unnecessary `useEffect` patterns, upgrades TypeScript types, applies isc-web conventions. Uses `opus` model. |
| `claude-settings-sync` | Syncs `~/.claude/` with this repo. Finds untracked files in `~/.claude/`, moves them to `~/proj/claude/`, creates symlinks, and commits/pushes changes. |
| `cross-app-expert` | Expert in changes that span multiple Instacart apps (partners, IPP, customers-backend). Knows when a change in one app requires coordinated changes in others — proto updates, RPC interface changes, shared data model changes. |
| `customers-backend-expert` | Expert in the customers-backend (v4) Rails app — domain-driven design, 80+ domain gems, Sorbet type annotations, RPC patterns, and the v3 legacy app migration. |
| `docs-keeper` | Maintains the work log in `~/notes/claude-docs/`. Determines the active hiiro task, creates or appends timestamped log entries, and loads prior context when resuming work. |
| `dotfiles-sync` | Keeps `~/proj/home/` (cross-machine) and `~/proj/home-ic/` (work machine) in sync with actual dotfiles. Handles drift checking, copying changes, and commits. |
| `endpoint-expert` | Expert in adding API endpoints to partners (REST), customers-backend (RPC), and retailer-platform-api (GraphQL + Hub). Knows controller patterns, serializers, resolvers, mutations, Pundit policies, and request specs for each app. |
| `git-coordinator` | Central coordinator for all git workflow. Ties together worktrees, branches, PRs, hiiro task tracking, tmux sessions, and disk space management. The go-to agent for any git operation. |
| `hiiro-expert` | Expert in the hiiro CLI for task/worktree management. Ensures code changes are made in the correct worktree. Invoke when creating/switching tasks, setting up worktrees, managing tmux sessions, or when the `/hiiro` skill is used. |
| `ic-resources-expert` | Expert in Instacart internal tooling: ISC (services, tasks, confs, deploys), Temporal workflows, Glean search, Slack, Atlassian (Confluence + Jira), AWS S3, and CLI tools (gohan, bento, graft, pastry, olive, croissant, hiiro). |
| `instacart-docs` | Expert in creating and parsing Instacart engineering documents — ERDs (Engineering Review Documents) and RCAs (Root Cause Analyses). Knows the required sections, templates, and skills for each doc type. |
| `ipp-expert` | Expert in the IPP (Instacart Platform Portal) — retailer-platform-web-workspace (React/TypeScript), retailer-platform-graphql-mesh (API gateway), and retailer-platform-api (Rails/GraphQL backend). |
| `lint-specs-expert` | Expert in linting rules, spec writing, and Buildkite CI failures for partners, customers-backend, and IPP. Knows RuboCop configs, custom cops, ESLint rules, SimpleCov requirements, and spec patterns for each app. |
| `partners-expert` | Expert in the partners Rails app — whitelabel sites, launch onboardings, batch ingestions, partner configurations, FLIP features, SSO, POSOI, Temporal workflows, and the RBAC system. |
| `store-config-expert` | Expert in adding fields to the store configuration schema end-to-end: Ruby T::Struct schema, TypeScript types, GraphQL fragments (with codegen), IPP SC Admin UI, and optional backfill rake tasks. |
| `task-project-manager` | Manages tasks and projects using hiiro. Lists in-flight tasks, triages new work into the right task/subtask, maintains work logs, and generates status reports across concurrent tasks. |
| `tooling-advisor` | Identifies friction in development workflows and recommends concrete improvements — new agents, skills, hooks, or CLAUDE.md instructions. Invoke when a task takes many iterations, an error recurs, or a workflow feels slow. |
| `worktree-expert` | Expert in creating git worktrees with sparse checkout for the carrot monorepo. Always checks disk space first (the `~/work` disk is chronically near capacity) and enforces sparse checkout to prevent disk exhaustion. |

---

## Commands

Commands are slash commands invoked as `/command-name [args]`. They live in `commands/`.

| Command | Description |
|---------|-------------|
| `/backup-prompt` | Saves the current prompt as a timestamped markdown file to `~/claude/prompts/backups/`. Useful for preserving complex prompts before running them. |
| `/fix-pr [PR]` | Diagnoses PR build failures via Buildkite, classifies each failure as related or unrelated to your changes, presents a fix plan, applies selected fixes, runs local verification, and pushes. |
| `/josh [args]` | Debug/diagnostic command. Dumps environment variables and session info to `~/notes/slash-test/` for troubleshooting Claude Code session context. |
| `/josh-code-review [PR]` | Generates a comprehensive HTML code review report for a PR. Checks out the PR locally for deep context, then produces a styled report covering architecture, testing, and clarity. Saves to `~/notes/prs/`. |
| `/pr-blitz [deadline]` | Queues an `/agent-party` fix job for every open PR with failing or pending checks. Reads task context from hiiro and claude-docs, then populates each task's hiiro queue with a targeted fix prompt. |
| `/prcr [PR]` | Full PR code review: fetches diff and metadata in parallel, checks out locally for large PRs, generates a styled HTML report, uploads to Pastry, and posts an auto-generated comment on the PR. |
| `/project-status` | Generates a full project status report — all tasks and PRs grouped by project in merge order, with next steps and copy-paste prompts. Converts to HTML via `mdoc` and opens in browser. |
| `/refactor [scope]` | Applies a comprehensive set of refactoring principles (composition over inheritance, abstraction levels, noun-based naming, value objects, DRY, etc.) to the specified code. Supports `scope:dirty` and `scope:branch`. |
| `/save-prompt [slug]` | Exports the current Claude session as a formatted "Terminal Noir" HTML file with a table of contents, collapsible tool calls, and anchor links. Saves to `~/claude/prompts/exports/`. |

---

## Skills

Skills are reusable, invocable modules that live in `skills/`. They provide reference documentation and structured workflows.

| Skill | Description |
|-------|-------------|
| `check` | Runs lint and test commands on changed files in the monorepo. Detects which app the files belong to (partners, customers-backend, IPP), installs dependencies if needed, and auto-fixes linting issues where possible. Invoke with `/check`. |
| `hiiro` | Full reference for the hiiro CLI — task/worktree management, the Claude prompt queue (`h queue`), and PR tracking (`h pr`). Includes all command signatures, config file locations, and usage patterns. |
| `onboarding-attributes` | Manages the `VALID_ATTRIBUTES_FOR_APPROVAL_MAP` in the partners app — adding, editing, and archiving onboarding attributes; managing form structure and navigation across backend and IPP frontend. Critical rules: never delete attributes, never rename them. |
| `personal-repos` | Context and agent guidance for maintaining `~/proj/claude/` (Claude config) and `~/proj/home/` (dotfiles). Describes when to invoke each sync agent and the typical workflow for both repos. |

---

## Repo Structure

```
agents/          # Sub-agent definitions (.md files with frontmatter)
commands/        # Slash command definitions (.md files)
skills/          # Reusable skill modules (each a directory with SKILL.md)
settings.json    # Claude Code settings (symlinked from ~/.claude/settings.json)
settings.local.json
script/
  setup          # Moves files to repo and creates symlinks in ~/.claude/
  preview        # Dry-run: shows what setup would do
```

## Syncing

```bash
# Preview what needs syncing
~/proj/claude/script/preview

# Apply sync (move files, create symlinks)
~/proj/claude/script/setup

# Commit tracked changes
cd ~/proj/claude
git add agents/ commands/ skills/ settings.json
git commit -m "sync: <description>"
git push
```
