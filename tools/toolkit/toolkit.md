---
command: toolkit
script: toolkit/toolkit.py
description: Manage and discover toolkit utilities
version: 1.0.0
category: toolkit
---

# toolkit

Manage and create tools within the toolkit.

## Installation

```bash
cd /data/repos/toolkit
make install
which toolkit
```

## Usage

### Create New Tool

```bash
# Create tool with default category (toolkit)
toolkit create toolname

# Create tool in specific category
toolkit create toolname --category document
toolkit create newtool --category search
```

### Options

```bash
toolkit create TOOLNAME [options]

Options:
  TOOLNAME              Name of the tool to create (required)
  --category CATEGORY   Tool category (default: toolkit)
  -h, --help            Show help message
```

## What It Does

The `toolkit create` command:
1. Creates a new Python file `tools/<category>/<toolname>.py`
2. Adds basic tool template with argparse structure
3. Updates `pyproject.toml` with new tool entry
4. Creates `__init__.py` if needed

## Tool Template

New tools are created with:
- Proper shebang and docstring
- Argument parser setup
- Main function structure
- CLI entry point

## Examples

### Create Document Tool

```bash
toolkit create xml2md --category document
```

Creates: `tools/document/xml2md.py` and updates `pyproject.toml`

### Create Search Tool

```bash
toolkit create epub-extractor --category search
```

### Create New Category

```bash
# First create the category directory
mkdir -p tools/media
touch tools/media/__init__.py

# Then create tool in that category
toolkit create video-converter --category media
```

## After Creating a Tool

1. **Edit the generated file** - Add your tool logic
2. **Install the toolkit** - Run `make install`
3. **Test your tool** - Run `<toolname> --help`
4. **Create documentation** - Add `<toolname>.md` in the category directory

## Features

- **Quick scaffolding** - Creates boilerplate instantly
- **Auto-configuration** - Updates pyproject.toml automatically
- **Consistent structure** - All tools follow same pattern
- **Category organization** - Tools grouped by function

## Notes

- Tool names should be lowercase with hyphens
- Category must be a valid directory under `tools/`
- After creation, run `make install` to use the new tool
- Tool is immediately available after install
