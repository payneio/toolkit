# Personal Toolkit Framework

A structured approach to managing personal utility scripts following the Unix philosophy while leveraging Python's ecosystem.

## Philosophy

This framework follows key Unix philosophy principles:

1. **Each tool does one thing well** - Create small, focused utilities
2. **Use text streams as universal interface** - Tools accept stdin and output to stdout
3. **Compose tools through pipes** - Chain tools together for complex workflows
4. **Make it easy to combine tools** - Standardized formats (JSON, YAML) for data exchange

While maintaining the simplicity of Unix tools, we leverage Python's rich ecosystem for more complex functionality, managed through UV for dependency management.

## Directory Structure

```
~/toolkit/
├── bin/              # Launcher scripts
├── tools/            # Individual utilities
│   ├── calendar/     # Calendar-related tools
│   │   ├── add.py
│   │   └── list.py
│   ├── email/        # Email-related tools
│   │   └── fetch.py
│   └── sms/          # SMS-related tools
│       └── parse.py
├── src/              # Shared library code
│   └── toolkit/    
│       ├── __init__.py
│       ├── calendar_utils.py
│       └── parsers.py
├── tests/            # Test directory
├── pyproject.toml    # Project metadata and dependencies
└── README.md         # This file
```

## Setup

### Prerequisites

- Python 3.8+
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/toolkit.git ~/toolkit
   ```

2. Build and install tools:
   ```bash
   cd ~/toolkit
   make all
   ```

3. Ensure `~/.local/bin` is in your PATH:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

## Creating New Utilities

The toolkit provides a simple workflow for creating new utilities using the `make` system.

### Creating a new tool with the make system

The easiest way to create a new tool is to use the `new-tool` make target:

```bash
cd ~/toolkit
make new-tool name=newtool
```

This will:
1. Create the tool directory structure
2. Add a template Python script with proper docstrings
3. Create the tools.toml configuration file
4. Generate the man page
5. Create the bin launcher script

### Tool Configuration File (tools.toml)

Each tool includes a `tools.toml` configuration file:

```toml
[tool]
command = "mytool"
script = "mytool/mytool.py"
description = "Description of the tool"
version = "1.0.0"
system_dependencies = ["optional-system-dependency"]
```

This configuration is used by the `make` system to generate bin launchers and man pages.

### Tool Implementation Pattern

A typical tool follows this pattern:

```python
#!/usr/bin/env python3
"""
mytool: Description of the tool

Detailed explanation of what the tool does.

Usage: mytool [options]

Examples:
  mytool input.txt           # Process a file
  cat input.txt | mytool     # Process stdin
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Tool description")
    parser.add_argument('input', nargs='?', help="Input file (default: stdin)")
    parser.add_argument('-v', '--version', action='version', version='mytool 1.0.0')
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

### Running with cron

```
# Run daily at 9am
0 9 * * * $HOME/.local/bin/fetch-email | $HOME/.local/bin/extract-events | $HOME/.local/bin/cal-add > $HOME/logs/schedule-$(date +\%Y\%m\%d).log 2>&1
```

## Managing Complexity

As your collection grows to hundreds or thousands of utilities:

1. **Categorize by domain**: Group related tools in subdirectories
2. **Use consistent interfaces**: Standardize on input/output formats
3. **Share code**: Move common functionality to the `src/` directory
4. **Document well**: Maintain clear usage examples for each tool
5. **Consistent naming**: Establish naming patterns (e.g., `domain-verb`)

## Development Workflow

The toolkit framework provides make targets for common development tasks:

```bash
# Navigate to toolkit directory
cd ~/toolkit

# Run all the tasks (build, generate bin scripts, man pages, install)
make all

# Regenerate bin launchers
make bin

# Generate man pages
make man

# Build and sync dependencies
make build

# Run linting
make check

# Install symlinks to ~/.local/bin
make install-links

# Install man pages
make install-docs

# Clean up generated files
make clean
```

You can also run tests with:

```bash
uvx pytest
```

## Tool Discovery and Help

The toolkit includes a built-in help system to discover and learn about available tools:

```bash
# List all available tools
toolkit

# Get detailed information about a specific tool
toolkit --info gpt

# Get JSON output of all tools
toolkit --json
```
