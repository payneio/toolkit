# Search Tool

A modular, low-resource, local search system for files (PDFs, images, videos, etc.) where each **collection** is self-contained and can be indexed and queried using Tantivy.

## Overview

The `search` tool creates self-contained collections with their own configuration, extraction logic, and indexes. This allows for easy backup, sharing, and portability of searchable document collections.

## Key Concepts

### Collection
- A collection is any directory containing a `.search/` subdirectory.
- It is considered self-contained: all index metadata, config, and cache reside within `.search/`.

### Directory Structure
```
collection/
├── somefile.pdf
└── .search/
    ├── config.toml      # Describes extractors, patterns, etc.
    ├── cache/           # YAML/JSON metadata per source file
    ├── index/           # Xapian index (created by system)
```

## Commands

### Initialize a Collection

```bash
search init [directory]
search init --name "Research" ~/papers
search init --include "*.pdf" "*.md" --exclude "draft_*" "*.bak"
search init --extract "*.pdf=pdf2md {input}"
```

Creates a new search collection with:
- `.search/config.toml` - Configuration file
- `.search/cache/` - Directory for extracted metadata
- `.search/index/` - Directory for Xapian index

### Find Collections

```bash
search scan [directory]
```

Recursively walks a directory tree to find all valid collections (those containing `.search/config.toml`).

### Index Files in a Collection

```bash
search index [directory...]
search index --verbose ~/documents ~/papers
```

For each file in the collection that matches include/exclude patterns:
1. Finds the appropriate extractor based on file type
2. Executes the extractor to get metadata
3. Saves metadata to cache (optional)
4. Indexes the content and metadata with Tantivy

### Search Indexed Collections

```bash
search query "neural networks"
search query "DNA" --in ~/papers
search query "protein" --tag biology
search query "machine learning" --limit 10 --verbose
```

Searches across one or more collections using Tantivy's built-in scoring.

## Extractors

Extractors are shell commands that process files and output structured data (YAML or JSON). They must:
- Accept an input file path (supports template substitution with `{input}`)
- Output structured data on stdout
- Include at least one of: `title`, `tags`, or `content`

Example output:
```yaml
title: "Deep Learning for Genomics"
tags: ["ai", "genomics"]
content: "This paper discusses neural networks applied to DNA..."
custom:
  rating: 5
```

The search tool uses these extractors to create searchable content. It includes default extractors for common file types, but you can define custom extractors for any file type.

## Configuration

The `.search/config.toml` file controls how the collection works:

```toml
name = "Research Collection"

[include]
patterns = ["*.pdf", "*.mp4", "*.md"]

[exclude]
patterns = ["draft_*", "*.bak"]

[extractors]
"*.pdf" = "pdf2md {input}"
"*.md"  = "cat {input}"
"*.mp4" = "video-extract --output yaml {input}"

[output]
format = "yaml"
directory = "cache"
```

## Dependencies

- tantivy-py: Tantivy search engine Python bindings
- pyyaml: YAML parsing/serialization
- toml: TOML configuration parsing
- (optional) watchdog: For real-time indexing

### Installing Tantivy on Ubuntu

Tantivy is a full-text search engine library written in Rust. The Python bindings require rust for building.

```bash
# Install rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Add Rust to your PATH (or restart your shell)
source "$HOME/.cargo/env"
```

3. Install tantivy-py using pip:
   ```bash
   uv add tantivy-py
   ```

## Examples

### Create and use a research papers collection:

```bash
# Initialize a collection for research papers
$ mkdir ~/papers
$ search init --name "Research Papers" ~/papers

# Add some PDF extractors  
$ search init --extract "*.pdf=pdf2md {input}" ~/papers

# Index the papers
$ search index ~/papers

# Search for papers about machine learning
$ search query "machine learning" --in ~/papers
```

### Create a media collection with custom extractors:

```bash
# Initialize a collection for media files
$ search init --name "Media Collection" --include "*.mp4" "*.mp3" "*.jpg" ~/media

# Add custom extractors
$ search init --extract "*.mp4=ffmpeg -i {input} -f ffmetadata -" ~/media
$ search init --extract "*.jpg=exiftool -j {input}" ~/media

# Index the media files
$ search index ~/media

# Search for videos about cats
$ search query "cat" --in ~/media
```

## Troubleshooting

### No results when searching

1. Verify the collection is properly indexed:
   ```bash
   search scan ~/papers
   search index --verbose ~/papers
   ```

2. Check that extractors are working:
   - Manually run the extractor to ensure it produces valid output:
     ```bash
     pdf2md yourfile.pdf
     ```

3. Validate the Tantivy index:
   ```bash
   ls -la ~/papers/.search/index/
   ```
   
### Extractors failing

1. Ensure all dependencies are installed for your extractors
2. Test extractors manually to verify they work:
   ```bash
   pdf2md yourfile.pdf
   ```

3. Use the `--verbose` flag when indexing to see detailed errors:
   ```bash
   search index --verbose ~/papers
   ```
