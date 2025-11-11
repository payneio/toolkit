---
command: search
script: search/search.py
description: Manage self-contained searchable collections of files
version: 1.0.0
category: search
---

# search

Fast full-text search using Tantivy search index. Index and search documents with blazing speed.

## Installation

```bash
cd /data/repos/toolkit
make install
which search
```

## Usage

### Index Documents

```bash
# Index a directory
search index /path/to/documents

# Index specific files
search index file1.txt file2.pdf file3.docx
```

### Search

```bash
# Simple search
search query "search terms"

# Search with field
search query --field title "document title"

# Limit results
search query --limit 10 "search terms"
```

### Options

```bash
search index [paths...]        Index files or directories
search query [options] QUERY   Search indexed documents

Query options:
  QUERY                 Search query (required)
  --field FIELD         Search specific field (title, body, path)
  --limit N             Maximum results to return (default: 20)
  -h, --help            Show help message
```

## Features

- **Fast searching** - Powered by Tantivy search engine
- **Multiple formats** - Supports PDF, DOCX, TXT, and more
- **Full-text search** - Search entire document contents
- **Field search** - Search specific fields
- **Relevance ranking** - Results sorted by relevance

## Examples

### Index and Search

```bash
# Index your documents
search index ~/Documents

# Search for terms
search query "important meeting notes"
search query "project proposal 2024"
```

### Field-Specific Search

```bash
# Search in title only
search query --field title "Annual Report"

# Search in body
search query --field body "quarterly results"
```

### Batch Operations

```bash
# Index multiple directories
search index ~/Documents ~/Downloads ~/Desktop

# Incremental indexing
search index ~/Documents/new_files
```

## Supported File Types

- **Text files** - .txt, .md, .log
- **PDF documents** - .pdf
- **Word documents** - .docx
- **Other formats** - via text extractors

## Index Location

Index is stored in `~/.local/share/search/index` by default.

## Tips

- Index documents once, search many times
- Re-index when documents change
- Use quotes for exact phrases
- Field searches are faster for specific needs

## Notes

- Initial indexing may take time for large collections
- Index size depends on document collection size
- Supports incremental indexing
- UTF-8 text encoding recommended
