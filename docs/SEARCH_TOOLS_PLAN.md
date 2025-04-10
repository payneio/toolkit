# Collections

## **Design Document: Self-Contained Searchable Collections with Extractors**

### **Overview**
The goal is to build a modular, low-resource, local search system for files (PDFs, images, videos, etc.) where each **collection** is self-contained and can be indexed and queried using Tantivy. Each collection will contain configuration, extraction logic, and its own Tantivy index — allowing easy backup, sharing, and portability.

---

## **Key Concepts**

### **Collection**
- A collection is any directory containing a `.search/` subdirectory.
- It is considered self-contained: all index metadata, config, and cache reside within `.search/`.

### **.search/ Directory Contents**
```
collection/
├── somefile.pdf
└── .search/
    ├── config.toml        # Describes extractors, patterns, etc.
    ├── cache/             # YAML/JSON metadata per source file
    ├── index/             # Tantivy index (created by system)
```

---

## **Tool Design: Unified `search` Command**

Instead of implementing multiple separate tools, we will create a single `search` tool with subcommands. This provides a cleaner user experience and follows modern CLI design patterns.

### **Subcommands**

#### **1. `search init`**
Initializes a directory as a search collection.

- Creates `.search/config.toml` with:
  - `include` and `exclude` patterns
  - `extractors` mapping file globs to commands
- Creates `.search/cache/` and `.search/index/` directories.
- Adds a stub/default extractor command (optional).

#### **Example: config.toml**
```toml
name = "Research Collection"

[include]
patterns = ["*.pdf", "*.mp4", "*.md"]

[exclude]
patterns = ["draft_*", "*.bak"]

[extractors]
"*.pdf" = "pdf-extract --format yaml"
"*.md"  = "md-extract --format yaml"
"*.mp4" = "video-extract --output yaml"

[output]
format = "yaml"
directory = "cache"
```

#### **2. `search scan`**
Recursively walks a directory tree to find all valid collections (i.e., those containing `.search/config.toml`). Yields paths to each.

---

#### **3. `search index`**
Indexes or re-indexes all relevant files in one or more collections.

**Process:**
1. Load `.search/config.toml`.
2. Filter source files using `include` and `exclude`.
3. For each matched file:
   - Determine matching extractor based on glob.
   - Execute extractor via shell, substituting `{input}` with file path.
   - Capture stdout, parse as YAML or JSON.
   - Save structured metadata to `.search/cache/filename.yaml` (optional).
   - Add document to `.search/index/` via Xapian.

**Requirements:**
- Gracefully skip missing/invalid extractors.
- Detect unchanged files via timestamps or hashing (future optimization).

### **Extractors**
External CLI tools defined per file type. Must:
- Accept an input file path.
- Output structured data in YAML or JSON.
- Support `{input}` template substitution (system will handle it).

**Example Output:**
```yaml
title: "Deep Learning for Genomics"
tags: ["ai", "genomics"]
content: "This paper discusses neural networks applied to DNA..."
custom:
  rating: 5
```

**Required fields for indexing:**
- `title` (optional)
- `tags` (optional)
- `content` (optional)
- Any extra fields are optional and can be stored in Xapian's `doc.set_data()`.

#### **4. `search query`**
Queries one or more collections using Xapian’s built-in scoring and returns ranked results.

**Options:**
- Search content, title, tags
- Filter by tags
- Limit result count

**Example CLI usage:**
```bash
search query "neural networks" --tag ai --in ~/papers/
```

---

## **Tantivy Usage**
Each `.search/index/` holds a standalone Tantivy index.

- Use `path` as a unique ID (i.e., source file path).
- Index `title`, `content`, `tags`.
- Tags are stored as facets for efficient filtering.
- Extra fields can be stored in JSON format.

---

## **Implementation Notes**
- Use `watchdog` (optional) for real-time reindexing.
- Use `subprocess.run()` to call extractor commands.
- Use `fnmatch` or `pathlib.match()` to match file patterns.
- Use `tomli` or `tomlkit` to parse `config.toml`.
- CLI entrypoints can use `argparse` or `click`.
- Use Python bindings for Tantivy via `tantivy-py`.

---

## **Future Enhancements**
- Global search across all collections.
- Smart caching using mtime or content hash.
- GUI or TUI interface with `textual`.

---

## **Summary**
This system builds modular, indexable file collections, each with their own config and extractor logic. Extractors are CLI tools that output YAML/JSON. The system handles indexing and search via Tantivy, storing everything locally for backup and portability. Tantivy provides a Rust-based, high-performance full-text search engine with excellent performance characteristics and Python bindings.

Let me know if you'd like this formatted as a markdown doc or split into dev tickets.

