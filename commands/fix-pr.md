---
description: Diagnose PR build failures and return fix plan for plan mode
---

# /fix-pr

Diagnose all PR build failures and produce an actionable fix plan.

## Workflow Overview

| Step | Action | Tool |
|------|--------|------|
| 0 | Get failed checks | `gh pr checks` |
| 1 | Parse Buildkite URLs | Extract org/pipeline/build |
| 2 | Get failed jobs | `mcp__buildkite__get_build` |
| 3 | Parallel analysis | Launch `buildkite-analyzer` agents |
| 4 | Collect results | `TaskOutput` |
| 5 | Synthesize | Combine results into fix plan |
| 6 | Select fixes | `AskUserQuestion` |
| 7 | Local verification | `/lint`, `/test`, `pesto update` |

---

## Step 0: Get Failed Checks

```bash
gh pr checks --json name,state,link | jq '[.[] | select(.state == "FAILURE")]'
```

**No PR?** Exit with: "No PR found for current branch. Push changes or create PR first."

**No failures?** Exit with: "All checks passing - no failures to diagnose."

---

## Step 1: Parse Buildkite URLs

Extract from pattern: `buildkite.com/{org}/{pipeline}/builds/{number}`

Example:
```
https://buildkite.com/instacart/griffin/builds/7967
→ org_slug: instacart
→ pipeline_slug: griffin
→ build_number: 7967
```

Skip non-Buildkite URLs (GitHub Actions, etc.) - note them as "non-Buildkite check".

---

## Step 2: Get Failed Jobs

For each failed Buildkite build:

```
mcp__buildkite__get_build
- org_slug, pipeline_slug, build_number
- detail_level: "summary"
- job_state: "failed,broken,canceled,timed_out"
```

Extract for each failed job:
- job_id (UUID)
- job_name
- state

**Warning threshold:** If >5 failed jobs total, use AskUserQuestion:

```json
{
  "questions": [{
    "question": "Found X failed jobs. How would you like to proceed?",
    "header": "Analysis",
    "options": [
      {
        "label": "Analyze all (Recommended)",
        "description": "Investigate all X failures for complete diagnosis"
      },
      {
        "label": "Analyze first 5 only",
        "description": "Faster analysis, may miss related failures"
      },
      {
        "label": "Cancel",
        "description": "Exit without analysis"
      }
    ],
    "multiSelect": false
  }]
}
```

If "Cancel" selected, exit with: "Analysis cancelled by user."

---

## Step 3: Parallel Analysis

Launch `buildkite-analyzer` agents **in parallel** using Task tool:

```
For each failed job, use Task tool with:
- subagent_type: "buildkite-analyzer"
- run_in_background: true
- prompt: |
    org: {org_slug}
    pipeline_slug: {pipeline_slug}
    build_number: {build_number}
    job_uuid: {job_id}
    job_name: "{job_name}"
```

**Critical:** Launch ALL agents in a single message with multiple Task tool calls.

---

## Step 4: Collect Results

Use `TaskOutput` to wait for each agent:

```
TaskOutput
- task_id: {agent_id}
- block: true
- timeout: 60000
```

Parse JSON output from each agent.

---

## Step 5: Synthesize Fix Plan

Combine all agent outputs into actionable plan.

### Output Format

```markdown
## PR Build Failures

### Summary
- X failures across Y builds
- Types: [unique failure_types]

### Failures

| Job | Type | Root Cause | Location |
|-----|------|------------|----------|
| {job_name} | {failure_type} | {root_cause} | {file_location} |

### Fix Plan

1. [ ] Edit `{file}`: {suggested_fix}
2. [ ] Edit `{file2}`: {suggested_fix2}
3. [ ] Run: `{verification_command}`

### Verification

After applying fixes, run Step 7 local verification:
```bash
# Required verification (run in order)
pesto update           # Update BUILD files
make fmt               # Format code
/lint                  # Fix lint errors repo-wide
/test                  # Run tests for affected packages

# Then push and monitor
git add -A && git commit -m "Fix PR build failures" && git push
gh pr checks --watch
```
```

### Synthesis Rules

| Pattern | Action |
|---------|--------|
| Same file in multiple failures | Group into single fix item |
| compilation_error | Prioritize first (blocks other tests) |
| infrastructure failures | Note as "Re-run may resolve" |
| All failures have low confidence | Suggest manual investigation |
| Any code changes applied | Include Step 7 verification in fix plan |

---

## Step 6: Interactive Fix Selection

After displaying the fix plan, use AskUserQuestion to let the user select which fixes to address.

### 6.1 Group Fixes by Category

Group fixes into categories:

| Category | Patterns |
|----------|----------|
| Build Errors | `compilation_error`, `dependency` |
| Test Failures | `test_failure` |
| Lint Issues | `lint_error` |
| Infrastructure | `infrastructure`, `timeout` |

### 6.2 Present Fix Selection

**If ≤4 total fixes**, present individually:

```json
{
  "questions": [{
    "question": "Which fixes would you like to apply?",
    "header": "Fixes",
    "options": [
      {
        "label": "All fixes (Recommended)",
        "description": "Apply all X suggested fixes"
      },
      {
        "label": "[Build] Fix undefined: NewFetcher",
        "description": "controllers/query/fetcher.go:42"
      },
      {
        "label": "[Test] Fix TestFetch assertion",
        "description": "controllers/query/fetcher_test.go:89"
      },
      {
        "label": "[Lint] Fix hugeParam",
        "description": "controllers/query/config.go:15"
      }
    ],
    "multiSelect": true
  }]
}
```

**If >4 total fixes**, group by category:

```json
{
  "questions": [{
    "question": "Which fix categories would you like to apply?",
    "header": "Fixes",
    "options": [
      {
        "label": "All categories (Recommended)",
        "description": "Apply all X fixes across all categories"
      },
      {
        "label": "Build Errors (X fixes)",
        "description": "Fix compilation and dependency issues first"
      },
      {
        "label": "Lint Issues (Y fixes)",
        "description": "Fix lint errors (hugeParam, etc.)"
      },
      {
        "label": "Test Failures (Z fixes)",
        "description": "Fix failing test assertions"
      }
    ],
    "multiSelect": true
  }]
}
```

### 6.3 Handle Selection

| Selection | Action |
|-----------|--------|
| "All fixes" / "All categories" | Apply all suggested fixes |
| Specific fixes/categories | Apply only selected fixes |
| No selection (empty) | Exit with: "No fixes selected. Review the plan and run `/fix-pr` again when ready." |
| "Other" (custom) | Ask user to describe which fixes to apply |

### 6.4 Infrastructure Failures

If any failures are categorized as `infrastructure`:

```json
{
  "questions": [{
    "question": "Infrastructure failures detected. How to handle?",
    "header": "Infra",
    "options": [
      {
        "label": "Re-run CI (Recommended)",
        "description": "These often resolve on retry"
      },
      {
        "label": "Skip infrastructure issues",
        "description": "Focus on code issues only"
      },
      {
        "label": "Investigate anyway",
        "description": "Analyze infrastructure logs for patterns"
      }
    ],
    "multiSelect": false
  }]
}
```

---

## Step 7: Local Verification Before Push

After applying fixes, run local verification to catch issues before the next CI build.

### 7.1 Determine Required Checks

| Code Change Type | Required Verification |
|------------------|----------------------|
| Any Go code changes | `/lint`, `make fmt` |
| New/modified imports | `pesto update` |
| New/modified functions | `/test` (targeted or full) |
| BUILD.bazel changes | `pesto update`, targeted build |
| Interface changes | `make mockgen`, `/lint` |

### 7.2 Run Verification Commands

Execute in this order (each depends on previous):

1. **`make mockgen`** - Only if interfaces changed
2. **`pesto update`** - Update BUILD files (required if imports changed)
3. **`make fmt`** - Format all Go code
4. **`/lint`** - Fix lint errors across URSA repo
5. **`/test`** - Run tests for affected packages

**Critical**: Run against the **entire URSA repo**, not just modified files. CI runs full checks.

### 7.3 Present Verification Options

Use AskUserQuestion to let user select verification scope:

```json
{
  "questions": [{
    "question": "Run local verification before pushing?",
    "header": "Verify",
    "options": [
      {
        "label": "Full verification (Recommended)",
        "description": "Run /lint, make fmt, pesto update, /test for entire repo"
      },
      {
        "label": "Quick verification",
        "description": "Run /lint and make fmt only"
      },
      {
        "label": "Skip verification",
        "description": "Push changes without local verification"
      }
    ],
    "multiSelect": false
  }]
}
```

### 7.4 Execute Based on Selection

| Selection | Commands |
|-----------|----------|
| Full verification | `make mockgen` (if needed) → `pesto update` → `make fmt` → `/lint` → `/test` |
| Quick verification | `make fmt` → `/lint` |
| Skip verification | Proceed directly to commit/push |

After verification completes:
```bash
git add -A && git commit -m "Fix PR build failures" && git push
gh pr checks --watch
```

---

## Error Recovery

| Error | Recovery |
|-------|----------|
| No PR found | Exit with message to create/push PR |
| No failed checks | Exit with success message |
| Buildkite URL parse fails | Skip that check, continue with others |
| Agent times out | Include partial results, note incomplete |
| All agents fail | Suggest manual investigation with Buildkite URLs |
| No Buildkite failures | Note only non-Buildkite checks failed |
| Verification fails | Fix new errors before pushing, re-run verification |

---

## Example Output

```markdown
## PR Build Failures

### Summary
- 3 failures across 1 build
- Types: test_failure, compilation_error

### Failures

| Job | Type | Root Cause | Location |
|-----|------|------------|----------|
| Build | compilation_error | undefined: NewFetcher | controllers/query/fetcher.go:42 |
| Unit Tests | test_failure | TestFetch: expected 5, got 0 | controllers/query/fetcher_test.go:89 |
| Lint | lint_error | hugeParam: cfg is 256 bytes | controllers/query/config.go:15 |

### Fix Plan

1. [ ] Edit `controllers/query/fetcher.go:42`: Add missing NewFetcher function or fix import
2. [ ] Edit `controllers/query/fetcher_test.go:89`: Update test expectation or fix mock setup
3. [ ] Edit `controllers/query/config.go:15`: Pass Config by pointer instead of value
4. [ ] Run: `bazel test //customers/ursa/controllers/query/...`

### Verification

After applying fixes, run Step 7 local verification:
```bash
pesto update           # Update BUILD files
make fmt               # Format code
/lint                  # Fix lint errors repo-wide
/test                  # Run tests for affected packages

git add -A && git commit -m "Fix PR build failures" && git push
gh pr checks --watch
```
```
