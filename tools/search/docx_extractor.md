---
command: docx-extractor
script: search/docx_extractor.py
description: Extract content and metadata from Word .docx files
version: 1.0.0
category: search
system_dependencies:
- pandoc
---

# docx-extractor

Extract text from Microsoft Word (.docx) documents.

## Installation

```bash
cd /data/repos/toolkit
make install
which docx-extractor
```

## Usage

```bash
# Extract from Word doc
docx-extractor document.docx

# Save to file
docx-extractor document.docx > text.txt

# Multiple documents
docx-extractor file1.docx file2.docx
```

### Options

```bash
docx-extractor [files...]

Options:
  files       DOCX files to extract text from
  -h, --help  Show help message
```

## Features

- Extract text from .docx files
- Handles headers, footers, and body text
- Preserves basic structure
- Fast extraction

## Examples

```bash
# Single document
docx-extractor report.docx

# Batch extraction
for file in *.docx; do
    docx-extractor "$file" > "${file%.docx}.txt"
done

# Search extracted text
docx-extractor document.docx | grep "keyword"
```

## Notes

- Only supports .docx format (not .doc)
- Formatting is stripped
- Tables become plain text
- Images are not extracted
