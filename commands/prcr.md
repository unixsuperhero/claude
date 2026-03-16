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

2. **In parallel** (run all of these at the same time, use /agent-party — do NOT wait for one before starting the next):
   - Fetch PR metadata: `gh pr view PRNUMBER --repo OWNER/REPO --json number,title,author,state,body,baseRefName,headRefName,labels,reviews,reviewRequests,additions,deletions,changedFiles,commits,url`
   - Fetch unified diff: `gh pr diff PRNUMBER --repo OWNER/REPO`
   - List changed files: `gh pr view PRNUMBER --repo OWNER/REPO --json files`

3. **Fast path check**: If the PR has <= 8 changed files AND <= 400 lines total (additions+deletions), skip the local checkout entirely and proceed directly to analysis using only the diff. This is the fast path.

4. **Full path only** (skip if fast path): Run `gh pr checkout PRNUMBER` in the /Users/josh/work/code-review/main worktree to get a local copy for deeper context. Only do this for larger/more complex PRs where reading surrounding code is necessary.

5. Analyze the unified diff holistically (not commit-by-commit — analyze the complete change as a whole). The unified diff from step 2 contains all changes. Focus the review on the diff output directly.

6. Generate comprehensive code review HTML report

7. Save report to /Users/josh/notes/prs/ directory

8. Open it with `open report.html`

9. Upload the report to Pastry and capture the URL:
   ```bash
   PASTRY_JSON=$(pastry create <report-file> --title "PR #PRNUMBER Code Review" --json)
   PASTRY_URL=$(echo "$PASTRY_JSON" | jq -r '.url // "https://pastry.instacart.com/\(.slug)"')
   ```
   Use the actual report file path saved in step 7 and the PR number parsed in step 1.

10. Post a comment on the PR with a disclosure and link to the report:
    ```bash
    gh pr comment PRNUMBER --repo OWNER/REPO --body "$(cat <<'EOF'
    > 🤖 **Auto-generated comment** — This code review report was automatically generated and posted by Claude Code. It has not been manually reviewed.

    📋 **[Full review report](PASTRY_URL)**
    EOF
    )"
    ```
    Substitute `PRNUMBER`, `OWNER/REPO`, and `PASTRY_URL` with the actual values.

**Review Report Output:**

The generated HTML report should include:

- PR metadata (title, author, status, etc.)
- **PROMINENT link to the PR on GitHub in the header section (not buried at the bottom)**
- Summary of what the PR does
- Praise section (good practices observed)
- Issues by priority (Critical, Important, Suggestion) with file paths and line numbers
- Overall assessment

**Design & Styling Requirements:**

Use this refined technical editorial aesthetic with excellent accessibility:

**Color System (CSS Variables):**
```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0e14;
  --bg-secondary: #151a23;
  --bg-tertiary: #1d242f;

  /* Text - all WCAG AA+ compliant */
  --text-primary: #e6edf3;    /* 18.5:1 contrast */
  --text-secondary: #9198a1;  /* 7.8:1 contrast */
  --text-muted: #6e7681;      /* 4.6:1 contrast */

  /* Semantic colors */
  --critical: #ff6b6b;
  --critical-bg: #2d1517;
  --important: #ffa94d;
  --important-bg: #2d2317;
  --suggestion: #4dabf7;
  --suggestion-bg: #15232d;
  --praise: #51cf66;
  --praise-bg: #172d1a;

  /* Accents */
  --accent-primary: #748ffc;
  --accent-secondary: #ff8787;
  --border-primary: #2d333b;
  --border-secondary: #373e47;
}
```

**Typography:**
- Display font: 'Red Hat Display' (technical, geometric) from Google Fonts
- Body font: 'DM Sans' from Google Fonts
- Monospace: 'JetBrains Mono' for code

**Header Layout:**
- Header must have dark background with subtle gradient
- PR title as h1, large and bold
- **GitHub PR link displayed prominently as a styled button/badge immediately under the title**
- Metadata grid below the link (author, status, branch, labels, changes, reviewers)

**Issue Cards:**
- 4px left border with severity color
- Matching tinted background (e.g., critical uses --critical-bg)
- Clear severity label and icon
- File path in monospace font
- Good padding and spacing

**Accessibility:**
- All text meets WCAG AA contrast ratios minimum
- Links underlined on hover
- Clear focus states for keyboard navigation
- Severity indicated by color + shape + text (not color alone)

**Do not comment on:**

- Linting or formatting issues (handled by CI)
- Minor stylistic preferences

<!--
ORIGINAL WORKFLOW (pre-optimization):
1. Parse PR number/repo
2. mcp__github__pull_request_read get (metadata)
3. gh pr checkout in code-review worktree (always)
4. mcp__github__pull_request_read get again (redundant - same as step 2)
5. Analyze each commit sequentially (N sequential API calls)
6. Generate report
7. Save + open

OPTIMIZATIONS MADE:
- Merged redundant steps 2+4 (were identical API calls)
- Parallelized metadata fetch + diff fetch + files list (all independent)
- Replaced sequential per-commit analysis with single unified diff review
- Added fast path: skip checkout entirely for small PRs (<= 8 files, <= 400 lines)
- Removed commit-by-commit section from report (replaced with holistic analysis)
-->
