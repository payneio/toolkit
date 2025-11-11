# html2text

Convert HTML content to plain text, removing HTML tags while preserving basic structure and formatting. Works well with email content.

## Installation

```bash
# Install the toolkit
cd /data/repos/toolkit
make install

# Verify installation
which html2text
```

## Usage

### Basic Usage

```bash
# Convert HTML file to text
html2text email.html

# Convert from stdin
cat email.html | html2text

# Convert ProtonMail HTML email to text
protonmail read email.eml | html2text
```

### Options

```bash
html2text [options] [file]

Options:
  -h, --help     Show help message
  file           HTML file to convert (optional, reads from stdin if not provided)
```

## Features

- **Preserves structure** - Maintains paragraphs, lists, and headings
- **Handles links** - Converts `<a>` tags to readable format
- **Terminal friendly** - Formatted output suitable for terminal viewing
- **Pipe support** - Works with stdin/stdout for command chaining
- **Email optimized** - Works well with HTML email content

## Examples

### Convert HTML file

```bash
html2text newsletter.html > newsletter.txt
```

### Use with ProtonMail

```bash
# Read HTML email as plain text
protonmail read 2024-07-17_01-14-40_*.eml | html2text
```

### Process multiple files

```bash
for file in *.html; do
    html2text "$file" > "${file%.html}.txt"
done
```

### Use in a pipeline

```bash
curl https://example.com | html2text | less
```

## Output Format

The converter:
- Removes all HTML tags
- Preserves paragraph breaks
- Formats lists with bullets/numbers
- Shows links in readable format: `Link Text (https://url)`
- Maintains code blocks and preformatted text
- Converts headers to emphasized text

## Notes

- Skips `<head>`, `<style>`, and `<script>` tags
- Decodes HTML entities (e.g., `&amp;` becomes `&`)
- Wraps long lines for better readability
- Works with both complete HTML documents and fragments
