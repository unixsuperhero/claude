---
name: openlink
description: This skill should be used when the user asks to "open this link", "open these URLs", "open in browser", or pastes one or more URLs and wants them opened. Use the `open` CLI tool to open each URL individually.
version: 0.1.0
---

# Open Links in Browser

Open one or more URLs using the macOS `open` CLI tool.

## Usage

Call `open` once per URL — passing multiple URLs to a single `open` call only opens the first one:

```bash
open <url1>
open <url2>
open <url3>
```

Run each as a separate Bash call, or chain them with `&&`.
