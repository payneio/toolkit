# Personal Toolkit Framework

A structured approach to managing personal utility scripts following the Unix philosophy while leveraging Python's ecosystem.

## Philosophy

This framework follows key Unix philosophy principles:

1. **Each tool does one thing well** - Create small, focused utilities
2. **Use text streams as universal interface** - Tools accept stdin and output to stdout
3. **Compose tools through pipes** - Chain tools together for complex workflows
4. **Make it easy to combine tools** - Standardized formats (JSON, YAML) for data exchange

While maintaining the simplicity of Unix tools, we leverage Python's rich ecosystem for more complex functionality, managed through UV for dependency management.

### Discovering Tools

Use the `toolkit` command to explore available tools:

```bash
# List all available tools
toolkit list

# Show detailed information about a specific tool
toolkit info gpt

# Get JSON output for scripting
toolkit list --json
toolkit info docx2md --json
```

## Setup

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

  ```bash
  git clone https://github.com/yourusername/toolkit.git ~/toolkit
  cd ~/toolkit
  make all
  uv tool install --editable .
  ```

### System Dependencies

Some tools require system packages to be installed separately. These dependencies are listed in each tool's markdown documentation frontmatter under the `system_dependencies` field.

Use `toolkit list --verbose` to see which tools have system dependencies, then refer to the tool's documentation for installation instructions.

## Creating New Utilities

The toolkit provides a streamlined workflow for creating new utilities using the `toolkit create` command.

```bash
# Create a new tool in its own category
toolkit create my-tool --description "Description of my tool"

# Add a tool to an existing category
toolkit create newtool --category document --description "Document processing tool"
```

This automatically:
1. Creates the tool directory structure
2. Generates a Python script with proper template
3. Creates markdown documentation with YAML frontmatter metadata
4. Updates pyproject.toml with the tool entry

After creation, just edit the implementation and run `make install` to use your new tool.

## Tools Configuration System

Tools are defined using Python's standard `[project.scripts]` configuration in [pyproject.toml](pyproject.toml), which allows UV to install them as executable commands.

**Key Design Feature**: Each tool has a single markdown file containing both metadata (YAML frontmatter) and documentation. This design:
- Eliminates duplication between configuration and documentation files
- Provides a single source of truth for tool metadata
- Uses industry-standard YAML frontmatter format (like Jekyll, Hugo, Docusaurus)
- Makes tool discovery automatic via the `toolkit` command

Each tool includes a markdown documentation file with YAML frontmatter for metadata:

```markdown
---
command: my-tool
script: my-tool/my_tool.py
description: Description of the tool
version: 1.0.0
category: my-tool
system_dependencies:
  - optional-system-dependency
---

# my-tool

Tool documentation here...
```

The markdown frontmatter is used for documentation and the `toolkit` discovery command. The actual installation is handled by the `[project.scripts]` section in pyproject.toml.

### Single Source of Truth

Each tool has one markdown file containing both metadata (in YAML frontmatter) and comprehensive documentation. This ensures consistency and makes maintenance easier.

### Tool Implementation Pattern

A typical tool follows this pattern:

```python
#!/usr/bin/env python3
"""
my-tool: Description of the tool

Detailed explanation of what the tool does.

Usage: my-tool [options]

Examples:
  my-tool input.txt           # Process a file
  cat input.txt | my-tool     # Process stdin
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tool description")
    parser.add_argument('input', nargs='?', help="Input file (default: stdin)")
    parser.add_argument('-v', '--version', action='version', version='my-tool 1.0.0')
    args = parser.parse_args()
    
    # Read from stdin or file
    if args.input:
        with open(args.input) as f:
            data = f.read()
    else:
        data = sys.stdin.read()
    
    # Process data
    result = process_data(data)
    
    # Output results to stdout
    print(result)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Adding Dependencies

Add any new dependencies to `pyproject.toml` and then run `make build`:

```toml
[project]
name = "toolkit"
version = "0.1.0"
dependencies = [
  "requests>=2.28.0",
  "beautifulsoup4>=4.11.0",
  "toml>=0.10.2",
  # Add new dependencies here
]

[project.optional-dependencies]
dev = [
  "pytest>=7.0.0",
  "ruff>=0.11.4",
]
```

## Usage Patterns

### Basic usage

Run any utility by its name:

```bash
cal-add
cal-list
fetch-email
```

### Piping between utilities

Chain tools together using Unix pipes:

```bash
# Extract events from email and add to calendar
fetch-email | extract-events | cal-add

# With filtering
fetch-email | grep "important" | extract-events | cal-add
```

### Using files as intermediate storage

```bash
# Save outputs to files
fetch-email > emails.json
extract-events < emails.json > events.json
cal-add < events.json
```

### Task Automation with systemd

The toolkit includes the `schedule` tool for managing systemd user timers and services. This provides a modern, robust alternative to cron for task automation:

```bash
# Enable linger so timers run even when logged out
loginctl enable-linger $USER

# Schedule a task to run every 5 minutes
schedule add my-task \
    --command "my-script" \
    --schedule "5min" \
    --description "Run my script every 5 minutes" \
    -e "API_KEY=secret123"

# View scheduled tasks
schedule list

# Check task status
schedule status my-task

# View task logs
schedule logs my-task --follow
```

**Common schedules:**
- Intervals: `5min`, `1hour`, `2h`, `1day`, `1week`
- Named: `hourly`, `daily`
- Calendar: `--on-calendar "*-*-* 02:00:00"` (2 AM daily)

**Example: Auto-sync ProtonMail every 5 minutes**
```bash
schedule add protonmail-sync \
    --command "protonmail sync" \
    --schedule "5min" \
    --condition-command "pgrep -f 'protonmail-bridge'" \
    -e "PROTONMAIL_USERNAME=user@protonmail.com" \
    -e "PROTONMAIL_API_KEY=your-bridge-api-key"
```

See [tools/system/SCHEDULE.md](tools/system/SCHEDULE.md) for complete documentation.

## Managing Complexity

As your collection grows to hundreds or thousands of utilities:

1. **Categorize by domain**: Group related tools in subdirectories
2. **Use consistent interfaces**: Standardize on input/output formats
3. **Share code**: Move common functionality to the `src/` directory
4. **Document well**: Maintain clear usage examples for each tool
5. **Consistent naming**: Establish naming patterns (e.g., `domain-verb`)

## Makefile Build System

The toolkit uses a Makefile to automate common tasks, making it easy to maintain and extend the toolkit.

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make all` | Build and install tools |
| `make build` | Sync dependencies with UV |
| `make install` | Install tools with uv tool install |
| `make uninstall` | Uninstall toolkit tools |
| `make check` | Run linting and type-checking |
| `make test` | Run all tests |
| `make clean` | Clean up generated files |

### How the Build System Works

1. **Dependency Management**: Uses UV for Python dependency management
2. **Tool Installation**: Installs tools as executable commands via pyproject.toml
3. **Tool Discovery**: The `toolkit` command discovers tools via markdown frontmatter
4. **Quality Control**: Runs ruff for linting/formatting and pyright for type-checking

### Example Development Workflow

```bash
# Navigate to toolkit directory
cd ~/toolkit

# Create a new tool (creates .py and .md with frontmatter)
toolkit create mynewcalc

# Edit the tool implementation
vim tools/mynewcalc/mynewcalc.py

# Update documentation and metadata
vim tools/mynewcalc/mynewcalc.md

# Run linting and type-checking
make check

# Install/reinstall the tool
make install

# Test your tool
mynewcalc --help

# List all available tools
toolkit list
```

You can also run tests with:

```bash
uvx pytest
```

## Additional Resources

For more detailed information:
- **Tool Creation Guide**: See [docs/TOOL_CREATION_GUIDE.md](docs/TOOL_CREATION_GUIDE.md) for comprehensive tool development instructions
- **Individual Tool Documentation**: Each tool has its own `.md` file with detailed usage examples
- **Category READMEs**: Check category-specific README files for domain-specific workflows
