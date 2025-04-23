# mdscraper

A tool to combine text files from a directory into a single Markdown document.

## Features

- Scans directories for text files and combines them into a single markdown document
- Supports filtering through .gitignore-style configuration files
- Can recursively process subdirectories
- Generates a table of contents
- Handles file name or file path inclusion as headers
- Automatically ignores binary files
- Outputs to file or stdout

## Usage

```bash
# Basic usage - outputs to stdout
mdscraper [directory]

# Save output to a file
mdscraper -o output.md [directory]

# Recursively process subdirectories
mdscraper -r [directory]

# Add table of contents
mdscraper --toc [directory]

# Use a custom ignore file
mdscraper --ignore-file .myignore [directory]

# Include full file paths in headers
mdscraper --include-path [directory]

# Don't add headers for each file
mdscraper --no-headers [directory]
```

## Filter File Format

Create a `.mdscraper` file in the directory you want to process. The format follows .gitignore patterns:

```
# Comments start with #
*.log      # Ignore all log files
temp/      # Ignore directories named 'temp'
!important.log  # Except for important.log
```

## Examples

```bash
# Create a single markdown from all text files in current directory
mdscraper -o combined.md .

# Create a document with table of contents, recursively processing all subdirectories
mdscraper -r --toc -o documentation.md ~/project/

# Process a specific directory with a custom ignore file
mdscraper --ignore-file .custom-ignore -o output.md ~/notes/
```