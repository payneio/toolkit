# Search Tools

Tools for indexing and searching documents.

## Tools

### [search](search.md)

Fast full-text search using Tantivy search engine. Index and search documents with blazing speed.

**Quick start:**
```bash
search index ~/Documents
search query "search terms"
```

### [text-extractor](text_extractor.md)

Extract text from text files.

```bash
text-extractor document.txt
```

### [pdf-extractor](pdf_extractor.md)

Extract text from PDF documents.

```bash
pdf-extractor document.pdf
```

### [docx-extractor](docx_extractor.md)

Extract text from Word documents.

```bash
docx-extractor document.docx
```

## Typical Workflow

```bash
# 1. Extract text from various formats
pdf-extractor report.pdf > report.txt
docx-extractor proposal.docx > proposal.txt

# 2. Index documents
search index ~/Documents

# 3. Search
search query "important project information"
```

See individual tool documentation for full details.
