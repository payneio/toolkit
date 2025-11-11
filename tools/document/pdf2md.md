---
command: pdf2md
script: document/pdf2md.py
description: Convert PDF files to Markdown
version: 1.0.0
category: document
system_dependencies:
- pandoc
- poppler-utils
---

# pdf2md

Convert PDF documents to Markdown format with text extraction and formatting preservation.

## Installation

```bash
cd /data/repos/toolkit
make install
which pdf2md
```

## Usage

```bash
# Convert single PDF
pdf2md document.pdf

# Output to specific file
pdf2md document.pdf -o output.md

# Convert from stdin
cat document.pdf | pdf2md > output.md
```

### Options

```bash
pdf2md input.pdf [-o output.md]

Options:
  input.pdf           Input PDF document
  -o, --output FILE   Output markdown file (default: stdout)
  -h, --help          Show help message
```

## Features

- Extracts text from PDFs
- Preserves basic formatting where possible
- Handles multi-page documents
- Works with text-based PDFs
- Pipe-friendly output

## Examples

```bash
# Convert and save
pdf2md report.pdf -o report.md

# Convert multiple PDFs
for file in *.pdf; do
    pdf2md "$file" -o "${file%.pdf}.md"
done

# Extract and search
pdf2md document.pdf | grep "keyword"
```

## Notes

- Works best with text-based PDFs
- Scanned PDFs (images) require OCR
- Complex layouts may lose some formatting
- Tables are converted to plain text
