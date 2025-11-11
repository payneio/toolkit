---
command: text-extractor
script: search/text_extractor.py
description: Extract content and metadata from text files
version: 1.0.0
category: search
---

# text-extractor

Extract plain text from various document formats.

## Installation

```bash
cd /data/repos/toolkit
make install
which text-extractor
```

## Usage

```bash
# Extract from file
text-extractor document.txt

# Extract to file
text-extractor document.txt > output.txt

# Process multiple files
text-extractor file1.txt file2.txt file3.txt
```

### Options

```bash
text-extractor [files...]

Options:
  files       Files to extract text from
  -h, --help  Show help message
```

## Supported Formats

- Plain text (.txt)
- Markdown (.md)
- Log files (.log)
- Other text-based formats

## Features

- Fast text extraction
- Handles multiple files
- Preserves text encoding
- Pipe-friendly output

## Examples

```bash
# Extract single file
text-extractor document.txt

# Batch processing
for file in *.txt; do
    text-extractor "$file" > "${file%.txt}_extracted.txt"
done

# Use in pipeline
text-extractor doc.txt | grep "keyword"
```
