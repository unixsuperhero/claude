---
description: Diagnose PR build failures, classify by relatedness, apply fixes, and push
---

# /fix-pr

Diagnose PR build failures in $ARGUMENTS, classify each as related or unrelated to your changes, apply the fixes, and push.

## Workflow Overview

| Step | Action | Tool |
|------|--------|------|
| 0 | Get failed checks | `gh pr checks` |
| 1 | Fetch PR diff for relatedness | `gh pr diff` |
| 2 | Parse Buildkite URLs | Extract org/pipeline/build |
| 3 | Verify Buildkite MCP | `mcp__buildkite__user_token_organization` |
| 4 | Parallel analysis | Launch `buildkite-analyzer` agents |
| 5 | Collect results | `TaskOutput` |
| 6 | Synthesize with relatedness | Classify RELATED vs UNRELATED |
| 7 | Select fixes | `AskUserQuestion` |
| 8 | Apply fixes | Read + Edit tool |
| 9 | Local verification | Auto-detect commands |
| 10 | Commit and push | Confirm with user |

---

## Step 0: Get Failed Checks

```bash
gh pr checks --json name,state,link | jq '[.[] | select(.state == "FAILURE")]'
```

Also capture:
```bash
PR_NUMBER=$(gh pr view --json number -q .number)
PR_URL=$(gh pr view --json url -q .url)
```

**No PR?** Exit: "No PR found for current branch. Push changes or create PR first."

**No failures?** Exit: "All checks passing — nothing to fix."

---

## Step 1: Fetch PR Diff for Relatedness

```bash
gh pr diff --name-only          # changed file paths
gh pr diff | head -c 100000     # diff content (capped)
```

Keep both in context — used in Step 6 to classify failures.

---

## Step 2: Parse Buildkite URLs

Extract from pattern: `buildkite.com/{org}/{pipeline}/builds/{number}`

```
https://buildkite.com/instacart/griffin/builds/7967
→ org_slug: instacart, pipeline_slug: griffin, build_number: 7967
```

Skip non-Buildkite URLs (GitHub Actions, etc.) — note them as "non-Buildkite check".

---

## Step 3: Verify Buildkite MCP

```
mcp__buildkite__user_token_organization
```

If unavailable:
> **Buildkite MCP not configured.** Run:
> ```bash
> claude mcp add --transport http buildkite https://mcp.buildkite.com/mcp/readonly
> ```
> Then run `/mcp` in Claude Code to authorize.

---

## Step 4: Parallel Analysis

Launch `buildkite-analyzer` agents **in parallel** using Task tool:

```
For each unique Buildkite build, use Task tool with:
- subagent_type: "pr:buildkite-analyzer"
- run_in_background: true
- prompt: |
    Analyze this failed Buildkite build:
    - org_slug: {org}
    - pipeline_slug: {pipeline}
    - build_number: {number}
    - build_url: https://buildkite.com/{org}/{pipeline}/builds/{number}

    Return a structured JSON diagnosis with failure type classification.
```

**Critical:** Launch ALL agents in a single message with multiple Task tool calls.

---

## Step 5: Collect Results

```
TaskOutput
- task_id: {agent_id}
- block: true
- timeout: 120000
```

Parse JSON output from each agent.

---

## Step 6: Synthesize with Relatedness

Combine all agent outputs. For each failure, use the PR diff and changed file list to classify:

**RELATED if any apply:**
- The failing file appears in the changed files list
- The error references a symbol/method/type/field added or modified in the diff (even if the failing file itself wasn't changed — e.g. a test for a model breaks when the PR adds a required field)
- Compilation or type error about something defined in the diff
- The test exercises a code path visibly changed by the diff

**UNRELATED if:**
- The failing file has no connection to changed files and the error references nothing in the diff
- Infrastructure failure (timeout, network, OOM) with no code-level error
- Error pattern clearly predates the PR

When in doubt, classify as **RELATED**. Better to offer an unnecessary fix than silently skip a real breakage.

### Output Format

```markdown
## PR #${PR_NUMBER} Build Failures

### Summary
- Failed checks: ${FAILED_COUNT}
- Related (fixable): ${RELATED_COUNT}
- Unrelated (skipped): ${UNRELATED_COUNT}

### Failures to Fix

| Job | Type | Root Cause | Location |
|-----|------|------------|----------|
| {job_name} | {failure_type} | {root_cause} | {file:line} |

### Fix Plan

1. [ ] `{file}:{line}` — {suggested_fix}
2. [ ] `{file2}:{line}` — {suggested_fix2}

### Unrelated Failures (for reference)

| Job | Type | Why Unrelated |
|-----|------|---------------|
| {job_name} | {failure_type} | {reason} |
```

### Synthesis Rules

| Pattern | Action |
|---------|--------|
| Same file in multiple failures | Group into single fix item |
| `compilation_error` | Prioritize first (blocks other tests) |
| Infrastructure/timeout failures | Note as "Re-run may resolve", exclude from fix list |
| All failures have low confidence | Suggest manual investigation |

---

## Step 7: Interactive Fix Selection

### Infrastructure/Timeout Check

If **all** related failures are `infrastructure` or `timeout`:
- Skip fix selection entirely
- Display: "All related failures are infrastructure or timeout issues — these cannot be fixed with code changes."
- Show each failure's Buildkite URL for manual retry
- Done.

If **some** are infrastructure/timeout, exclude them from the selection list and note: "Note: {N} infrastructure/timeout failure(s) not included — retry from the Buildkite dashboard if needed."

### Fix Selection UI

Build options dynamically from failure types actually present:

```json
{
  "questions": [{
    "question": "Which fixes would you like to apply?",
    "header": "Fix Selection",
    "options": [
      { "label": "Fix all ({N} issues)", "description": "Apply all recommended fixes" },
      { "label": "Test failures only ({N})", "description": "..." },
      { "label": "Lint/format only ({N})", "description": "..." },
      { "label": "Compilation errors only ({N})", "description": "..." },
      { "label": "Skip fixes — just show the analysis", "description": "..." }
    ],
    "multiSelect": false
  }]
}
```

Only include category options for types actually present. If only one fixable type exists, offer just "Fix all" and "Skip fixes".

**If ≤4 total fixes**, list each fix individually (multiSelect: true) instead of grouping by category.

---

## Step 8: Apply Fixes

For each fix in the selected category, in priority order:
1. Compilation errors
2. Type errors
3. Test failures
4. Lint errors
5. Format errors

**For each fix:**
1. **Read** the relevant file
2. **Apply** using the Edit tool
3. **Track** what was changed

---

## Step 9: Local Verification

After applying fixes, detect verification commands in this priority order:

1. `.isc/pipeline.yml` — parse for lint/test/build steps matching failure types
2. `Makefile` — find `.PHONY` targets: `test`, `fmt`, `lint`, `build`
3. `CLAUDE.md` — extract documented verification commands
4. `.claude/` — check for `/lint`, `/test` commands

**No detection found:**
```json
{
  "questions": [{
    "question": "No local verification commands detected. How would you like to proceed?",
    "header": "Verification",
    "options": [
      { "label": "Push and let CI re-run (Recommended)", "description": "Commit changes and push" },
      { "label": "Skip — I'll verify manually", "description": "Don't push, I'll handle it" }
    ]
  }]
}
```

**Detection found:**
```json
{
  "questions": [{
    "question": "How would you like to verify your fixes?",
    "header": "Local Verification",
    "options": [
      { "label": "Run local verification", "description": "Run: {detected_commands}" },
      { "label": "Push and let CI re-run", "description": "Skip local check, push to CI" },
      { "label": "Skip entirely", "description": "Don't verify or push" }
    ]
  }]
}
```

---

## Step 10: Commit and Push

If user chooses to push:

1. Stage only the changed files (not `git add -A`)
2. Generate a commit message summarizing the fixes applied
3. Confirm with user via AskUserQuestion before committing
4. Commit and push

```
Changes pushed. CI will re-run checks.
Monitor at: ${PR_URL}
```

---

## Error Recovery

| Error | Recovery |
|-------|----------|
| No PR found | Suggest creating/pushing PR first |
| All checks passing | Exit with success message |
| Buildkite MCP unavailable | Display setup instructions |
| Agent timeout | Report partial results, note incomplete |
| All agents fail | Suggest manual investigation with Buildkite URLs |
| No Buildkite failures | Note which checks are non-Buildkite, suggest manual review |
| Fix application fails | Report error, continue with remaining fixes |
| Local verification fails | Offer to push anyway or abort |
| All failures unrelated | Report all with context, exit without fix options |
| All failures infrastructure | Report with Buildkite dashboard links, exit without fix options |
