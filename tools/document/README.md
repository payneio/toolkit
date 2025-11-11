# Document Tools

Tools for converting between document formats.

## Tools

### [docx2md](docx2md.md)

Convert Microsoft Word (.docx) to Markdown.

```bash
docx2md document.docx -o output.md
```

### [pdf2md](pdf2md.md)

Convert PDF to Markdown.

```bash
pdf2md document.pdf -o output.md
```

### [md2pdf](md2pdf.md)

Convert Markdown to PDF.

```bash
md2pdf document.md -o output.pdf
```

### [html2text](html2text.md)

Convert HTML to plain text.

```bash
html2text page.html > page.txt
```

## Common Workflows

### Word to PDF via Markdown

```bash
docx2md document.docx | md2pdf -o document.pdf
```

### PDF to plain text

```bash
pdf2md document.pdf | html2text
```

### Batch conversion

```bash
# Convert all Word docs to Markdown
for file in *.docx; do
    docx2md "$file" -o "${file%.docx}.md"
done
```
