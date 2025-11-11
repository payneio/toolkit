---
command: docx2md
script: document/docx2md.py
description: Convert Word .docx files to Markdown
version: 1.0.0
category: document
system_dependencies:
- pandoc
---

# docx2md

Convert Microsoft Word (.docx) documents to Markdown format.

## Installation

```bash
cd /data/repos/toolkit
make install
which docx2md
```

## Usage

```bash
# Convert single file
docx2md document.docx

# Output to specific file
docx2md document.docx -o output.md

# Convert from stdin
cat document.docx | docx2md > output.md
```

### Options

```bash
docx2md input.docx [-o output.md]

Options:
  input.docx          Input Word document
  -o, --output FILE   Output markdown file (default: stdout)
  -h, --help          Show help message
```

## Features

- Preserves document structure (headings, lists, tables)
- Converts formatting (bold, italic, links)
- Handles images (extracts and references)
- Supports tables
- Maintains document hierarchy

## Examples

```bash
# Convert and save
docx2md report.docx -o report.md

# Convert multiple files
for file in *.docx; do
    docx2md "$file" -o "${file%.docx}.md"
done

# Pipe to other tools
docx2md document.docx | grep "important"
```
