# Claude Global Instructions

## Asking Questions

When asking a follow-up question or clarifying question, ALWAYS use the AskUserQuestion tool. Never ask questions in plain prose text.

## Work Logging

Keep a running log of all work in `~/notes/claude-docs/`.

- Use these docs to track progress and a history of everything done, including timestamps
- Work is grouped by the hiiro parent task or subtask (run `h task ls` to see current tasks)
- Each log file corresponds to a task or topic (e.g., `cutover-task2-sendgrid.md`, `saform-regex-notes.md`)
- When starting or resuming work on a task, check the relevant log file for prior context
- Append new entries with a timestamp (date + time) and brief description of what was done

### Log entry format
```
## YYYY-MM-DD HH:MM
- What was done
- Any decisions made, blockers, or next steps
```

### Current hiiro tasks (run `h task ls` to refresh)
- `oncall` / `oncall/posoi` / `oncall/propagation`
- `required-if-checks`
- `cutover` / `cutover/shutdown-date` / `cutover/banner` / `cutover/monitors` / `cutover/parmonitors`
- `cub`
- `saform` / `saform/keyword`

## Generating Reports and Documentation

When generating any report, analysis, summary, or document for the user:

1. **Write in markdown first** — use `~/claude/docs/` as a scratch area if needed, or write inline to a temp file
2. **Convert with `mdoc`** — always run:
   ```bash
   mdoc <file.md> --title "Title" --desc "One-line description"
   ```
   Add `--toc` for longer documents with multiple sections.
3. **`mdoc` handles everything else** — it converts via pandoc, updates the index at `~/claude/index.html`, and opens the HTML file in the browser automatically.

### mdoc flags
| Flag | Description |
|------|-------------|
| `--title "..."` | Override document title (default: first H1) |
| `--desc "..."` | Short description shown in the index |
| `--toc` | Inject a table-of-contents sidebar |
| `--no-open` | Skip opening in browser |
| `-` as filename | Read from stdin |

### Index
All generated docs are catalogued at `~/claude/index.html` (most recent first).
The metadata sidecar lives at `~/claude/index.json`.

---

## File Saving

NEVER save files to `/tmp`. Instead:
- Save to `~/notes/files/` for standalone files (reports, exports, CSVs, data dumps, etc.)
- Save somewhere else in `~/notes/` if that makes more contextual sense
- Save to wherever the user explicitly specifies (e.g. `~/claude/prompts`, a project directory, etc.)

### Index

Maintain `~/notes/files/INDEX` — a plain text file, one absolute path per line, oldest at top, newest at bottom. Update it every time a file is added to `~/notes/files/`.

---

## Resource Tracking

Whenever a resource is created or discovered, track it with hiiro immediately:

- **Any URL** (Jira ticket, Confluence doc, Slack thread, PR, build URL):
  ```bash
  h link add <url> --tag <tag>
  ```
- **Any branch** (after creating or checking out a branch):
  ```bash
  h branch tag <branch> <task-name>
  ```
- **Any PR** (after pushing and opening a PR):
  ```bash
  h pr track            # track current branch's PR
  h pr track 1234       # track by PR number
  ```
- **Tasks/subtasks**: use `h task` and `h subtask` commands (see Work Logging above)

## Common Pitfalls

### Buildkite MCP Auth is Broken
`BUILDKITE_TOKEN` is not available in Claude Code sessions — Buildkite MCP calls will always 401. Never attempt them. Instead:
- Use `gh pr checks <PR>` to get check status
- Use the `buildkite` skill (REST API via gh CLI) to fetch build logs
- Do NOT waste time retrying MCP calls after a 401

### Never Whole-Read Large Generated Files
These files are too large to read in full — always use Grep instead of Read:
- `pbgen/pbgen-ts/index.ts` (protobuf generated, 50K+ lines)
- `retailer-tools/*/src/api/index.ts` (GraphQL codegen, ~56K lines)
- Any file with "generated" or "codegen" in path/name
- `retailer-tools/retailer-platform-graphql-mesh/.meshrc.yml` (4K+ lines)
Use offset/limit for targeted reads, or Grep for specific patterns.

### Read Before Edit is Mandatory
ALWAYS Read a file before using Edit on it — even if you think you know its contents. This is especially critical in sub-agent contexts (agent-party teammates) where each agent has a fresh session context and Edit will fail without a prior Read.

### Never Search from Repo Root
The monorepo is very large. Always constrain Grep/Glob to a specific app subdirectory. Searching from `/Users/josh/work` will time out after 20 seconds. Examples:
- `partners/partners/` for the Partners app
- `retailer-tools/retailer-platform-web-workspace/` for IPP frontend
- `customers/customers-backend/` for Customers backend

### Check Branch/Worktree Existence Before Creating
Before running `h worktree create`, `git worktree add`, or any branch creation command, verify it doesn't already exist:
- `h wt ls` — list existing hiiro worktrees
- `git branch --list <name>` — check if a branch exists
If it already exists, check it out rather than creating a new one.

## Model and Thinking Selection

**Practical rule**: Before starting, ask: "Is this a lookup/simple edit (haiku), a standard dev task (sonnet), or something genuinely hard/novel (opus with thinking)?" Default to sonnet and only escalate when stuck.

**When to use extended thinking:**
- Novel algorithmic problems or complex architecture decisions with non-obvious trade-offs
- Debugging obscure issues where root cause is unclear after initial investigation
- Security-sensitive decisions
- DO NOT use for: routine CRUD, simple edits, well-understood patterns, looking up facts

**When to suggest a faster/smaller model:**
- Simple one-file edits with clear instructions → haiku
- Lookup/search tasks with no code generation → haiku
- Routine boilerplate generation → sonnet (default)
- Complex multi-file refactors, novel bugs, architecture → opus
- Current model is claude-sonnet-4-6; opus is available for hard problems

**Fast mode** (`/fast`): Toggle for faster output on straightforward tasks. Use when the task is clear and simple.
