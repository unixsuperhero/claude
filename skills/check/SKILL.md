---
name: check
description: Run lint and test commands on changed files in a monorepo. Detects which files changed, determines the app (partners, customers-backend, or IPP), and runs appropriate lint/test commands for JS/TS or Ruby files. Auto-fixes linting issues when possible. Use when invoked with /check command after code changes.
---

# Check

## Overview

Automatically detects changed files in your monorepo, determines which app they belong to (partners, customers-backend, or IPP), and runs the appropriate linting and testing commands. Handles both JavaScript/TypeScript and Ruby files with proper dependency installation and auto-fixing.

## Usage

Invoke this skill using the `/check` command after making code changes:

```
User: /check
```

The skill will:
1. Detect all changed files (staged, unstaged, and untracked)
2. Categorize them by app and file type
3. Run dependency installation if needed (`yarn` or `bundle install`)
4. Execute appropriate lint and test commands
5. Auto-fix linting issues when possible

## Supported Apps

### Partners App
- **Location**: `partners/partners/`
- **JS/TS**: `yarn lint --fix` and `yarn tests`
- **Ruby**: `bundle exec rubocop -a` and `bundle exec rspec`

### Customers Backend
- **Location**: `customers/customers-backend/`
- **Ruby**: `bundle exec rubocop -a` and `bundle exec rspec`

### IPP (Retailer Platform)
- **Location**: `retailer-tools/retailer-platform-web-workspace/`
- **JS/TS**: `yarn lint --fix` and `yarn tests`
- **Ruby**: `bundle exec rubocop -a` and `bundle exec rspec`
- **Additional**: `bento lint` (runs for any file type)

## Workflow

When invoked, execute the following:

1. **Run the orchestrator script**:
   ```bash
   python3 <skill-dir>/scripts/check_and_fix.py
   ```

2. **Interpret the output**:
   - ✅ Green checkmarks indicate passed checks
   - ❌ Red X's indicate failures
   - The script shows detailed output for each command

3. **Handle failures**:
   - Linting issues are auto-fixed where possible
   - Test failures require manual investigation
   - Review the output to understand what needs fixing

## Important Notes

- **Worktrees**: All directories under `~/work/` are worktrees of the main repo. Worktree names are typically 2 levels deep: `main_task/subtask/`
- **Working directory**: All commands are run from the respective app directory, not the repo root
- **Dependency checks**: The script automatically checks if `node_modules` or `vendor/bundle` exists before running commands
- **Auto-fix**: Rubocop runs with `-a` flag and linting runs with `--fix` to automatically correct issues
- **Timeouts**: Commands have a 5-minute timeout to prevent hanging

## Troubleshooting

If the script fails:
- Ensure you're in a git repository
- Check that the app directories exist at the expected paths
- Verify dependencies are installable (network access, correct Node/Ruby versions)
- Review error messages for specific command failures
