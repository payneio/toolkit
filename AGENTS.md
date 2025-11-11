# Agent Guide: Toolkit Project

This guide provides essential context for AI agents working with the toolkit project.

## Project Overview

A Python-based framework for creating, managing, and automating personal utility tools following Unix philosophy. Tools are installed system-wide via UV and can be piped together like standard Unix commands.

## Key Concepts

**Single Source of Truth**: Each tool has ONE `.md` file with YAML frontmatter containing metadata and full documentation. No separate config files.

**UV-Based Installation**: Tools are installed via `uv tool install --editable .` and become available system-wide in PATH.

**Categories**: Tools organized by domain (android, browser, document, email, gpt, mdscraper, search, system, toolkit).

## File Structure

```
tools/
├── <category>/
│   ├── <tool>.py          # Implementation
│   ├── <tool>.md          # Documentation + metadata (YAML frontmatter)
│   ├── test_<tool>.py     # Tests
│   └── README.md          # Category overview with quick-start examples
```

## Code Style Guidelines
- Imports: Standard library first, then third-party, then local modules. Don't put imports inside blocks, keep them at the top.
- Type annotations: Use type hints for function parameters and return values
- Naming: snake_case for functions/variables, PascalCase for classes
- Comments: Limit comments to explaining the "why" not the "how" or the "what". Make comments proper english and end with a period.
- Linting: Uses ruff for code quality checks
- Error handling: Use specific exceptions with descriptive messages, exit with sys.exit(1)
- Testing: Tests should be placed with the tools. Unittest with heavy mocking, tests prefixed with "test_"
- CLI: Use argparse with consistent flag patterns, support stdin/stdout piping
- Follow the Unix philosophy: Each tool does one thing well, text-based interfaces

## Best Practices
- Always prefer `uv add` to `uvx pip install`.

## Creating New Tools

**Use the toolkit command** (preferred):
```bash
toolkit create mytool --description "Tool description"
toolkit create mytool --category document --description "Description"
```

This automatically:
1. Creates directory structure
2. Generates Python template
3. Creates .md with frontmatter
4. Updates pyproject.toml

**Manual creation** (if toolkit unavailable):
1. Create `tools/<category>/<tool>.py`
2. Create `tools/<category>/<tool>.md` with frontmatter:
```yaml
---
command: tool-name
script: category/tool.py
description: Brief description
version: 1.0.0
category: category-name
system_dependencies:
  - optional-dependency
---
```
3. Add entry to `pyproject.toml` under `[project.scripts]`:
```toml
tool-name = "tools.category.tool:main"
```
4. Run `make install`

## Tool Implementation Pattern

```python
#!/usr/bin/env python3
"""
tool-name: Brief description

Detailed documentation here.

Usage: tool-name [options] [file]

Examples:
  tool-name input.txt
  cat input.txt | tool-name
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument('input', nargs='?', help="Input file (default: stdin)")
    args = parser.parse_args()

    # Read from stdin or file
    if args.input:
        with open(args.input) as f:
            data = f.read()
    else:
        data = sys.stdin.read()

    # Process and output
    result = process(data)
    print(result)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Essential Commands

### Build & Install
```bash
make all          # Build and install everything
make install      # Install tools to PATH
make check        # Run linting and type-checking
make test         # Run tests
uv add <package>  # Add dependency (never use pip)
```

### Tool Management
```bash
toolkit list              # List all tools
toolkit info <tool>       # Show tool details
toolkit create <name>     # Create new tool
```

### Schedule Tool (Systemd Automation)
```bash
schedule add <name> \
    --command "command to run" \
    --schedule "5min|hourly|daily" \
    -e "ENV_VAR=value"           # Environment variables (inline)

schedule list                    # List timers
schedule status <name>           # Check status
schedule logs <name> --follow    # View logs
schedule remove <name>           # Remove timer
```

**Important**: Systemd user units don't inherit shell env vars. Always pass environment variables inline with `-e` flags.

## Code Style Rules

- **Imports**: Standard lib, third-party, local. Always at top, never in blocks.
- **Type hints**: Use for all function parameters and returns
- **Naming**: snake_case (functions/vars), PascalCase (classes)
- **Comments**: Explain "why" not "what". Proper English with periods.
- **Error handling**: Specific exceptions, descriptive messages, `sys.exit(1)` on error
- **Testing**: unittest with mocking, test files prefixed `test_`
- **CLI**: argparse, support stdin/stdout piping
- **Dependencies**: Add to pyproject.toml, use `uv add`, never pip

## Common Tasks

### Modifying Existing Tool
1. Read `tools/<category>/<tool>.py`
2. Make changes
3. Update version in `tools/<category>/<tool>.md` frontmatter if significant
4. Run `make check` (linting/type-checking)
5. Run `make test` if tests exist
6. Run `make install` to reinstall

### Adding System Dependencies
Document in tool's .md frontmatter:
```yaml
system_dependencies:
  - pandoc
  - texlive-latex-base
```

### Creating Automated Tasks
Use `schedule` tool for systemd timers (preferred over cron):
```bash
# Enable linger first (allows timers when logged out)
loginctl enable-linger $USER

# Create timer with environment variables
schedule add backup-daily \
    --command "backup-collect" \
    --schedule "daily" \
    --on-calendar "*-*-* 02:00:00" \
    -e "BACKUP_DIR=/data/backups"
```

## Important Notes

1. **Always use `uv add`** to add dependencies, never pip
2. **Run `make check`** before committing changes
3. **Each tool needs its own .md file** with YAML frontmatter
4. **Update pyproject.toml** when creating new tools (or use `toolkit create`)
5. **Keep tests with tools** in same directory
6. **Support stdin/stdout** for all data processing tools
7. **Environment variables in systemd**: Pass inline with `-e` flags, not from shell

## Quick Reference

**File locations**:
- Tools: `tools/<category>/<tool>.py`
- Docs: `tools/<category>/<tool>.md`
- Tests: `tools/<category>/test_<tool>.py`
- Config: `pyproject.toml`

**Key files to update**:
- New tool → Update `pyproject.toml` [project.scripts]
- New dependency → Update `pyproject.toml` [project.dependencies]
- Tool docs → Update `tools/<category>/<tool>.md`

**After changes**:
1. `make check` - Verify code quality
2. `make test` - Run tests
3. `make install` - Reinstall tools
