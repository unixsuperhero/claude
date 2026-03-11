---
description: Review pull requests for architecture and design quality
---

Generate a comprehensive code review for pull request $ARGUMENTS (it should get 1 arg, the pr number) and output an HTML report.

**Review Focus:**

**Architecture & Design:**
- Separation of concerns and clear interfaces
- Code organization and structure
- Adherence to good programming practices

**Testing:**
- Test coverage for new/changed code
- Appropriate use of mocks and test doubles
- Test clarity and maintainability

**Clarity:**
- Unclear variable, function, or class names
- Complex logic that needs simplification

**Context**

If you are not given a Github owner, assume it's `instacart`. If the repo is
not specified, assume it's `carrot`.

Examples:

/prcr carrot#123 - should review instacart/carrot PR #123
/prcr 675148 - should review instacart/carrot PR #675148
/prcr haegin/graft#486 - should review haegin/graft PR #486

**Workflow:**

1. Parse the PR number and repository from $ARGUMENTS
2. Fetch PR metadata using `mcp__github__pull_request_read` method `get`
3. Use `gh pr checkout PRNUMBER` in /Users/josh/work/code-review/main worktree to get local copy
4. Fetch commits using `mcp__github__pull_request_read` method `get` to determine commit count
5. Analyze changes for each commit returned by the API
6. Generate comprehensive code review HTML report
7. Save report to /Users/josh/notes/prs/ directory
8. then open it with the open command like `open report.html`

**Review Report Output:**

The generated HTML report should include:

- PR metadata (title, author, status, etc.)
- Summary of what the PR does
- Praise section (good practices observed)
- Issues by priority (Critical, Important, Suggestion) with file paths and line numbers
- Commit-by-commit analysis
- Overall assessment

**Do not comment on:**

- Linting or formatting issues (handled by CI)
- Minor stylistic preferences
