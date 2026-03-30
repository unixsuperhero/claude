---
description: Generate an HTML document, save it to ~/claude/docs/, and update the index
---

# /mkdoc

Generate an HTML document and add it to the Claude docs index.

## Arguments

`$ARGUMENTS` may include a topic, title, or any description of what to generate.
If no arguments are given, ask the user what document to create.

## Step 1 — Choose a generation path

**Use the `mdoc` pipeline (default)** when the document is:
- A report, summary, status update, reference doc, or any prose/structured content
- Something that benefits from a consistent look matching the existing docs

**Use `/frontend-design`** when the document is:
- A rich interactive page, dashboard, or visual artifact
- Something that requires custom layout, charts, or bespoke styling beyond what pandoc produces
- After generating with `/frontend-design`, skip to Step 3 (write the file directly to `~/claude/docs/`)

---

## Step 2 — mdoc pipeline

Write the content as markdown to a temp file in `~/claude/docs/` (use a `.md` extension),
then convert it with:

```bash
mdoc <file.md> --title "Title Here" --desc "One-line description"
```

Add `--toc` for longer documents with multiple sections.
Add `--no-open` if the user does not want the browser to open.

`mdoc` will:
- Convert the markdown to styled HTML via pandoc using the `claude-docs.html` template
- Save the HTML to `~/claude/docs/YYYY-MM-DD-<slug>.html`
- Update `~/claude/index.json` and regenerate `~/claude/index.html`
- Open the file in the browser (unless `--no-open`)

Do not delete the intermediate `.md` file.

---

## Step 3 — Manual index update (frontend-design path only)

If you generated HTML directly (not via `mdoc`), you must update the index manually.

### Save the file

Save to: `~/claude/docs/YYYY-MM-DD-<slug>.html`

### Update index.json

Prepend a new entry to `~/claude/index.json`:

```json
{
  "title": "Document Title",
  "file": "docs/YYYY-MM-DD-<slug>.html",
  "date": "YYYY-MM-DD",
  "desc": "One-line description",
  "ts": "<ISO timestamp>"
}
```

### Regenerate index.html

Run `mdoc` on any dummy file with `--no-open` to trigger index regeneration,
OR update `~/claude/index.html` directly by editing the `<tbody>` rows and
the count/timestamp in the `<div class="meta">` header to match `index.json`.

---

## Notes

- Never save to `/tmp` — always use `~/claude/docs/` for the HTML output
- The `--desc` flag controls the subtitle shown in the index listing; make it informative
- Titles should be concise and scannable
- If `$ARGUMENTS` specifies a title or topic, use it; otherwise derive one from context
