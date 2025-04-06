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

2. Create symlinks to your utilities:
   ```bash
   mkdir -p ~/.local/bin
   cd ~/toolkit
   ./setup-links.sh
   ```

3. Ensure `~/.local/bin` is in your PATH:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   ```

## Creating New Utilities

### 1. Create a new utility script

```python
#!/usr/bin/env python3
# ~/toolkit/tools/calendar/add.py
"""
cal-add: Add an event to calendar
Usage: cal-add [options]
"""
import sys
import json
import argparse
from toolkit import calendar_utils

def main():
    parser = argparse.ArgumentParser(description="Add event to calendar")
    parser.add_argument('-f', '--file', help="Input file (default: stdin)")
    args = parser.parse_args()
    
    # Read from stdin or file
    if args.file:
        with open(args.file) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    # Process data
    result = calendar_utils.add_event(data)
    
    # Output results to stdout
    json.dump(result, sys.stdout)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 2. Create a launcher script

```bash
#!/usr/bin/env bash
# ~/toolkit/bin/cal-add

# Run with UV for automatic dependency management
uv run --project-dir ~/toolkit ~/toolkit/tools/calendar/add.py "$@"
```

### 3. Make both scripts executable

```bash
chmod +x ~/toolkit/tools/calendar/add.py
chmod +x ~/toolkit/bin/cal-add
```

### 4. Link to ~/.local/bin

```bash
ln -sf ~/toolkit/bin/cal-add ~/.local/bin/cal-add
```

### 5. Update dependencies

Add any new dependencies to `pyproject.toml`:

```toml
[project]
name = "toolkit"
version = "0.1.0"
dependencies = [
  "requests>=2.28.0",
  "beautifulsoup4>=4.11.0",
  # Add new dependencies here
]

[project.optional-dependencies]
dev = [
  "pytest>=7.0.0",
  "black>=22.0.0",
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

For active development:

```bash
# Navigate to scripts directory
cd ~/toolkit

# Install in development mode (if needed)
uv pip install -e .

# Run tests
uvx pytest

# Linting
uvx ruff

```

## Advantages of This Approach

- **Composability**: Tools work together through Unix pipes
- **Modularity**: Easy to add, modify, or replace individual tools
- **Dependency Management**: UV handles Python dependencies
- **Discoverability**: Commands available in PATH
- **Maintainability**: Organized structure scales to many utilities
- **Flexibility**: Works with cron, interactive use, and chaining