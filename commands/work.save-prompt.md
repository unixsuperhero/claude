---
description: Save the current session transcript to ~/claude/prompts/
---

Save the current session transcript in human-readable markdown format to `$HOME/claude/prompts/`.

1. Create the directory `$HOME/claude/prompts/` if it doesn't exist
2. Find this session's transcript file (look in `~/.claude/projects/` for the `.jsonl` file matching this session)
3. Convert the JSONL to human-readable html document and save to `$HOME/claude/prompts/` with a filename based on: $ARGUMENTS

If no name is provided, use the current date and a brief description of what the session was about (based on the conversation).

Format the filename as: `YYYY-MM-DD-{descriptive-slug}.md` (and `.html` for the HTML version)

## Conversion Format

Parse the JSONL and output blocks in html that are accordians so they can be
collapsed.  all of the tool entries should be collapsed by default.  but some
text should be visible with the tool name or some small description


it should probably be structured like:

```
> Human

prompt

  > Response

  response content

    > tool usage

    more info...
```

## Formatting rules

1. **Shell command grouping**: When showing shell commands with their output, group them in the same code block rather than separate Human/Assistant sections:

   Bad:
   ```markdown
   ## Human
   ```sh
   pwd
   ```

   ## Assistant
   ```
   /Users/myuser
   ```
   ```

   Good:
   ```markdown
   ```sh
   $ pwd
   /Users/myuser
   ```
   ```

   Use `$ ` prefix for the command to distinguish it from output.

3. **General readability**:
   - Remove redundant empty sections
   - Collapse consecutive tool calls when they're part of the same logical action
   - Skip meta messages and file-history-snapshot entries
   - Keep the conversation flow clear and scannable

## Content Parsing Rules

- Skip messages where `isMeta: true`
- Skip `file-history-snapshot` type entries
- Skip only the **last** `/save-prompt` invocation and everything after it: find the last user message containing `/save-prompt` or `save-prompt`, then exclude that message and all subsequent turns. Earlier `/save-prompt` calls that appear mid-session should be included normally — only the final one (the one triggering the current export) is excluded.
- For user messages: extract text from XML tags like `<bash-input>`, `<bash-stdout>`, show them clearly
- For assistant messages: show text blocks as-is, format tool_use blocks with the tool name and input
- Tool results appear as subsequent user messages with `tool_result` - associate them with the preceding tool call

## HTML Output

Generate an HTML version with:
- Basic styling for readability (code blocks, headers, etc.)
- Syntax highlighting for code blocks if possible
- Same content structure as the markdown version
- Save alongside the markdown file with `.html` extension

### Anchor links for sharing

Every turn and every tool/result accordion must have a unique `id` attribute so it can be linked to directly. Format:
- Conversation turns: `id="turn-{N}"` where N is the zero-based index
- Tool calls inside a turn: `id="turn-{N}-tool-{M}"` where M is the tool index within that turn
- Tool results: `id="turn-{N}-result-{M}"`

Each turn's role label (the header bar showing "👤 Human" or "🤖 Assistant") must include an anchor link `<a href="#{id}">` in the top-right corner that copies/navigates to that element. Style it as a subtle `#` symbol (e.g., `§` or `#`) that becomes visible on hover. Clicking it updates the URL hash so the link can be copied from the browser address bar.

Add a small JavaScript snippet that:
1. On page load, if there is a hash in the URL, scrolls to and opens (sets `open`) the matching `<details>` element and its parent `<details>` if nested.
2. When an anchor link is clicked, updates `window.location.hash` to the element's id.
