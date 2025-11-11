---
command: pdf-extractor
script: search/pdf_extractor.py
description: Extract content and metadata from PDF files
version: 1.0.0
category: search
---

# pdf-extractor

Extract text from PDF documents.

## Installation

```bash
cd /data/repos/toolkit
make install
which pdf-extractor
```

## Usage

```bash
# Extract from PDF
pdf-extractor document.pdf

# Save to file
pdf-extractor document.pdf > text.txt

# Multiple PDFs
pdf-extractor file1.pdf file2.pdf
```

### Options

```bash
pdf-extractor [files...]

Options:
  files       PDF files to extract text from
  -h, --help  Show help message
```

## Features

- Extract text from PDFs
- Handles multi-page documents
- Preserves text layout where possible
- Fast extraction

## Examples

```bash
# Single PDF
pdf-extractor report.pdf

# Batch extraction
for file in *.pdf; do
    pdf-extractor "$file" > "${file%.pdf}.txt"
done

# Search extracted text
pdf-extractor document.pdf | grep "keyword"
```

## Notes

- Works with text-based PDFs
- Scanned PDFs (images) require OCR
- Complex layouts may affect text order
