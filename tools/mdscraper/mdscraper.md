---
command: mdscraper
script: mdscraper/mdscraper.py
description: Combine text files from a directory into a single markdown document with
  .gitignore-style filtering
version: 1.0.0
category: mdscraper
---

# mdscraper

Convert web pages to clean Markdown format. Scrapes web content and converts to readable Markdown, removing ads and clutter.

## Installation

```bash
cd /data/repos/toolkit
make install
which mdscraper
```

## Usage

### Basic Usage

```bash
# Convert web page to Markdown
mdscraper https://example.com

# Save to file
mdscraper https://example.com > article.md

# Multiple URLs
mdscraper https://site1.com https://site2.com
```

### Options

```bash
mdscraper [options] URL [URL...]

Options:
  URL                 Web page URL to scrape (required)
  -o, --output FILE   Output file (default: stdout)
  --user-agent UA     Custom user agent string
  -h, --help          Show help message
```

## Features

- **Clean conversion** - Removes ads, navigation, footers
- **Markdown output** - Well-formatted Markdown
- **Main content extraction** - Focuses on article content
- **Link preservation** - Maintains links in Markdown format
- **Image handling** - Includes images with Markdown syntax
- **Fast** - Efficient scraping and conversion

## Examples

### Save Article

```bash
mdscraper https://blog.example.com/article > article.md
```

### Scrape Multiple Pages

```bash
# Scrape all pages
for url in $(cat urls.txt); do
    mdscraper "$url" > "$(echo $url | md5sum | cut -d' ' -f1).md"
done
```

### Convert for Reading

```bash
# Scrape and view
mdscraper https://news.site/article | less

# Scrape and convert to PDF
mdscraper https://article.com | md2pdf -o article.pdf
```

### With Custom User Agent

```bash
mdscraper --user-agent "MyBot/1.0" https://example.com
```

## Use Cases

- **Article archiving** - Save web articles as Markdown
- **Content migration** - Convert web content for static sites
- **Offline reading** - Download articles for later
- **Documentation** - Scrape docs to local Markdown
- **Research** - Collect and organize web content

## Output Format

Markdown output includes:
- Article title as H1
- Headings at appropriate levels
- Paragraphs with proper spacing
- Lists (ordered and unordered)
- Links in `[text](url)` format
- Images in `![alt](url)` format
- Code blocks when present

## Notes

- Respects robots.txt where possible
- Some sites may block scraping
- JavaScript-heavy sites may not work well
- Rate limit requests to avoid overwhelming servers
- Consider caching results for repeated access

## Troubleshooting

### Site Blocks Requests

Try using a custom user agent:
```bash
mdscraper --user-agent "Mozilla/5.0..." https://site.com
```

### JavaScript Content Missing

For JavaScript-heavy sites, consider using the `browser` tool instead:
```bash
browser "Go to URL and extract the article text"
```

### Rate Limiting

Add delays between requests:
```bash
for url in $(cat urls.txt); do
    mdscraper "$url" > file.md
    sleep 2
done
```
