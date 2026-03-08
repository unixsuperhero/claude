# Save Session as HTML

Export the current Claude session as a beautifully formatted HTML file.

## Instructions

Create an HTML file that displays this entire conversation session with the following structure and design:

### Structure
1. Generate a filename with timestamp and subject summary: `YYYYmmddHHMMSS-subject-matter.html`
   - The subject matter should be 2-3 words separated by hyphens summarizing the session's main topic
   - Example: `20260307181500-gitignore-setup.html` or `20260307190000-ruby-refactoring.html`
2. Save it to `~/claude/prompts/exports/` (create the directory if it doesn't exist)
3. Use the `open` command to preview it in the browser

### Table of Contents
- Add a **Table of Contents** section at the top, after the header
- List each exchange as a numbered link (e.g., `<a href="#exchange-1">`)
- Each link text should be a **concise 5-10 word summary** of what that Human prompt was about
- Style the TOC as a clean, scannable list with subtle styling matching the theme
- Example entries:
  - "Add .gitignore for sensitive Claude session data"
  - "Convert sync script to Ruby with symlinks"
  - "Create /save-prompt slash command"

### Content Organization
- Each Human message is a primary accordion section (expanded by default)
- **Add an `id` attribute to each exchange** for anchor linking (e.g., `id="exchange-1"`, `id="exchange-2"`)
  - Users can jump to specific exchanges via URL like `file.html#exchange-5`
- Inside each Human section, show the Assistant's response
- Tool calls/results should be nested accordions (collapsed by default)
- The Assistant's final text response should be prominently highlighted

### CRITICAL: Verbatim Content Preservation
- **NEVER rewrite, summarize, paraphrase, or abbreviate** the Human's prompts — include the full, exact text as written
- **NEVER rewrite, summarize, paraphrase, or abbreviate** the Assistant's responses — include the full, exact text as written
- The only content that may be summarized is the TOC link text (which is a brief label, not a replacement for the actual content)
- HTML-escape special characters (`<`, `>`, `&`, etc.) but do NOT alter the wording in any way
- If a message is long, that's fine — display it in full. Do NOT truncate or add "..." or "[continued]"

### Tool Call Details
For each tool call, include comprehensive details (all collapsed by default):
- **Tool name** prominently displayed in the summary
- **Input/Parameters**: Show the full parameters passed to the tool (file paths, commands, content)
- **Output/Result**: Show the actual result returned by the tool
- Format code/content in tool calls with proper syntax highlighting
- For file edits: show old_string and new_string
- For bash commands: show the command and its output
- For file reads/writes: show the file path and relevant content

### Design Direction: "Terminal Noir"
Create a dark, sophisticated interface inspired by retro terminals meets modern editorial design:

**Typography:**
- Use "JetBrains Mono" for code/technical content (via Google Fonts)
- Use "Playfair Display" for headers (via Google Fonts)
- Body text in "Source Sans 3"

**Color Palette (improved readability):**
- Background: Deep charcoal (#0a0a0a)
- Card backgrounds: Lighter gradient from #1e1e2e to #252540 for better contrast
- Human messages: Accent with warm amber (#f4a261)
- Assistant responses: Brighter cyan (#5ce1f5)
- Tool calls: Lighter purple (#9d4edd) with better text contrast
- Primary text: Bright off-white (#f5f5f5)
- Secondary/muted text: Light gray (#b0b0b8) - NOT too dark
- Code text: Bright cyan (#7df3ff) on darker backgrounds
- Tool result text: Light lavender (#d4c4e8) for readability

**Visual Details:**
- Subtle scan-line overlay effect on the background
- Cards have a soft glow/shadow effect
- Accordion headers have a subtle left border accent
- Smooth expand/collapse animations (300ms ease-out)
- Code blocks with syntax-highlighted appearance
- Timestamp badges in the corner of each exchange

**Layout:**
- Max-width container (900px) centered
- Generous padding and spacing
- Human prompts slightly indented from left
- Assistant responses have a distinct visual treatment
- Final response text gets a subtle spotlight effect (brighter background, larger text)

### HTML Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude Session - [TIMESTAMP]</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Playfair+Display:wght@600;800&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
  <style>
    /* CSS variables, reset, layout */
    /* Accordion styles */
    /* Animation keyframes */
    /* Scan-line effect */
    /* Card styles for Human/Assistant/Tool */
  </style>
</head>
<body>
  <div class="scanlines"></div>
  <main class="container">
    <header>
      <h1>Session Export</h1>
      <time>[TIMESTAMP]</time>
    </header>

    <!-- Table of Contents - links to each exchange -->
    <nav class="toc">
      <h2>Contents</h2>
      <ol class="toc-list">
        <li><a href="#exchange-1">Brief summary of what prompt #1 was about</a></li>
        <li><a href="#exchange-2">Brief summary of what prompt #2 was about</a></li>
        <!-- ... one entry per exchange -->
      </ol>
    </nav>

    <!-- For each Human/Assistant exchange - add id for anchor linking -->
    <article class="exchange" id="exchange-1">
      <details class="human-block" open>
        <summary><span class="label">Human</span> <time>#1</time></summary>
        <div class="human-content">
          <!-- Human message content (markdown rendered) -->
        </div>

        <div class="assistant-block">
          <div class="assistant-label">Assistant</div>

          <!-- Tool calls section (collapsed by default) -->
          <details class="tool-section">
            <summary><span class="tool-count">N tool calls</span></summary>
            <div class="tool-calls">
              <!-- Individual tool call accordions with full details -->
              <details class="tool-call">
                <summary><strong>ToolName</strong> — brief description</summary>
                <div class="tool-input">
                  <div class="tool-input-label">Input</div>
                  <pre><code><!-- Full parameters: file_path, command, old_string, new_string, etc. --></code></pre>
                </div>
                <div class="tool-output">
                  <div class="tool-output-label">Output</div>
                  <pre><code><!-- Full result/output from the tool --></code></pre>
                </div>
              </details>
            </div>
          </details>

          <!-- Final response (highlighted) -->
          <div class="final-response">
            <!-- Assistant's text response, prominently displayed -->
          </div>
        </div>
      </details>
    </article>

  </main>
  <script>
    /* Accordion behavior, smooth animations */
  </script>
</body>
</html>
```

### Execution

1. Read through the entire conversation context available to you
2. Build the HTML with all exchanges
3. Write the file with the timestamped name
4. Run: `open [filename]` to preview

Now generate the complete HTML file with all the conversation content from this session and open it.
