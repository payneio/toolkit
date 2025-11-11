---
command: html2text
script: document/html2text.py
description: Convert HTML content to plain text
version: 1.0.0
category: document
---

# html2text (document)

Convert HTML files to readable plain text, removing tags while preserving structure.

Note: This is the same tool as in the email category, available for document conversion tasks.

## Installation

```bash
cd /data/repos/toolkit
make install
which html2text
```

## Usage

```bash
# Convert HTML file
html2text page.html

# Convert from stdin
cat page.html | html2text

# Save to file
html2text page.html > page.txt
```

### Options

```bash
html2text [file]

Options:
  file        HTML file to convert (optional, reads from stdin if not provided)
  -h, --help  Show help message
```

## Features

- Removes HTML tags
- Preserves text structure
- Formats lists and paragraphs
- Converts links to readable format
- Terminal-friendly output

## Examples

```bash
# Convert web page
curl https://example.com | html2text

# Convert multiple files
for file in *.html; do
    html2text "$file" > "${file%.html}.txt"
done

# Extract article text
html2text article.html | less
```

See also: [email/html2text](../email/html2text.md) for email-specific usage.
