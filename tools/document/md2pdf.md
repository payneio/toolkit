---
command: md2pdf
script: document/md2pdf.py
description: Convert Markdown files to PDF
version: 1.0.0
category: document
system_dependencies:
- pandoc
- texlive-latex-base
---

# md2pdf

Convert Markdown documents to PDF format.

## Installation

```bash
cd /data/repos/toolkit
make install
which md2pdf
```

## Usage

```bash
# Convert single file
md2pdf document.md

# Output to specific file
md2pdf document.md -o output.pdf

# Convert from stdin
cat document.md | md2pdf > output.pdf
```

### Options

```bash
md2pdf input.md [-o output.pdf]

Options:
  input.md            Input Markdown document
  -o, --output FILE   Output PDF file (default: stdout)
  -h, --help          Show help message
```

## Features

- Converts Markdown to formatted PDF
- Preserves headings, lists, and formatting
- Supports code blocks
- Handles links
- Clean, readable PDF output

## Examples

```bash
# Convert and save
md2pdf README.md -o README.pdf

# Convert multiple files
for file in *.md; do
    md2pdf "$file" -o "${file%.md}.pdf"
done

# Create PDF from concatenated markdown
cat intro.md body.md conclusion.md | md2pdf -o complete.pdf
```

## Notes

- Supports standard Markdown syntax
- Some advanced Markdown features may not render
- PDF styling is fixed (no custom themes)
- Images referenced in Markdown should be accessible
