# Backup Prompt

Save the current prompt as a markdown file for later reference.

## Instructions

1. Look at the prompt that was submitted along with this `/backup-prompt` command
2. Remove the `/backup-prompt` portion from the content
3. Generate a filename with timestamp and subject summary: `YYYYmmddHHMMSS-subject-matter.md`
   - The subject matter should be 2-3 words separated by hyphens summarizing the prompt's main topic
   - Example: `20260307181500-api-refactor.md` or `20260307190000-fix-tests.md`
4. Save the markdown file to `~/claude/prompts/backups/` (create the directory if it doesn't exist)
5. Confirm to the user that the backup was saved with the full path

## Output Format

The backed up markdown file should contain:
- The full text of the user's prompt (minus the `/backup-prompt` command)
- Preserve all formatting, code blocks, and structure from the original prompt

## Example

If the user submits:
```
/backup-prompt

Please refactor the User model to use composition instead of inheritance.
Focus on extracting the authentication logic into a separate module.
```

Save to `~/claude/prompts/backups/20260307183000-user-model-refactor.md`:
```markdown
Please refactor the User model to use composition instead of inheritance.
Focus on extracting the authentication logic into a separate module.
```

Now backup the current prompt.
