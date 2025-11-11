# Toolkit Tool Creation Guide

This guide provides the essential steps and information needed to create a new tool for the toolkit framework.

## Recommended Approach: Use `toolkit create`

The easiest and recommended way to create a new tool:

```bash
# Create a new tool in its own category
toolkit create mytool --description "Description of my tool"

# Add a tool to an existing category
toolkit create newtool --category document --description "New document tool"
```

This automatically:
- Creates the Python script with proper template
- Creates markdown documentation with YAML frontmatter
- Updates pyproject.toml with the tool entry
- Sets up proper directory structure

Then just:
1. Edit `tools/<category>/<tool>.py` to implement functionality
2. Update `tools/<category>/<tool>.md` to enhance documentation
3. Run `make install` to install
4. Test with `<tool> --help`

## Manual Creation (Advanced)

For advanced users who want full control, here are the manual steps:

1. **Check for existing tools**
   - Run `toolkit list` to see all existing tools
   - Check if similar functionality already exists
   - Determine appropriate category or create new one

2. **Choose a name and description**
   - Use kebab-case for command names (e.g., `word-count`)
   - Select category directory or create new one (e.g., `text`)
   - Craft a clear, concise description

3. **Create directory structure**
   - Make a category directory if needed: `mkdir -p tools/<category>`
   - Create tool-specific directory ONLY if needed for complex tools: `mkdir -p tools/<category>/<toolname>`

4. **Create markdown documentation with frontmatter**
   - Each tool has its own markdown file at `tools/<category>/<tool-name>.md`
   - Add YAML frontmatter with metadata at the top
   - Include comprehensive documentation below the frontmatter

   ```markdown
   ---
   command: tool-name
   script: category/tool-name.py
   description: Clear description of what the tool does
   version: 1.0.0
   category: category
   system_dependencies:
     - optional-dependency
   ---

   # tool-name

   Tool documentation goes here...
   ```

5. **Create Python script**
   - Create script at `tools/<category>/<tool-name>.py`
   - Follow script template below
   - Ensure script is executable: `chmod +x tools/<category>/<tool-name>.py`

6. **Add to pyproject.toml**
   - Add tool entry to `[project.scripts]` section in pyproject.toml
   - Or use `toolkit create <tool-name>` to generate everything automatically
   - Format: `tool-name = "tools.category.tool_name:main"`

7. **Install and test**
   - Run `make install` to install the tool
   - Test with `tool-name --help`
   - Verify with `toolkit list` to see it in the available tools

## Python Script Template

```python
#!/usr/bin/env python3
"""
tool-name: Description of the tool

Detailed explanation of the tool's purpose and functionality.

Usage: tool-name [options] [arguments]

Examples:
  tool-name input.txt           # Basic usage example
  tool-name -o output.txt input.txt  # With options
  cat input.txt | tool-name     # Reading from stdin
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Description of the tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    # Add command-line arguments
    parser.add_argument('input', nargs='?', help="Input file (default: stdin)")
    parser.add_argument('-o', '--output', help="Output file (default: stdout)")
    parser.add_argument('-v', '--version', action='version', version='tool-name 1.0.0')
    args = parser.parse_args()
    
    # Read from stdin or file
    if args.input:
        with open(args.input, 'r') as f:
            data = f.read()
    else:
        data = sys.stdin.read()
    
    # Process data
    result = process_data(data)
    
    # Output to stdout or file
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
    else:
        print(result)
    
    return 0

def process_data(data):
    """Process the input data and return the result."""
    # Implement your tool's functionality here
    return data.upper()  # Example transformation

if __name__ == "__main__":
    sys.exit(main())
```

## Help Text Template

Your script's help text (shown with --help) should include:

1. A clear description of what the tool does
2. All command-line options explained
3. Example usages
4. Exit status codes
5. Related tools (if any)

Example help text format:
```
tool-name: Description of the tool

Detailed explanation of what the tool does, its purpose,
and how it fits into workflows.

Usage: tool-name [OPTIONS] [ARGUMENTS]

Options:
  -o, --output FILE      Write output to FILE instead of stdout
  -h, --help             Show this help message and exit
  -v, --version          Show version information and exit

Arguments:
  FILE                   Input file to process (default: reads from stdin)

Examples:
  tool-name input.txt                # Basic usage
  tool-name -o output.txt input.txt  # With output file
  cat input.txt | tool-name          # Reading from stdin

Exit Status:
  0  Success
  1  Error (various conditions)

See also: toolkit, related-tool
```

## Best Practices

1. **Follow Unix philosophy**
   - Do one thing well
   - Accept input from stdin when no file is specified
   - Output to stdout by default
   - Return 0 for success, non-zero for errors

2. **Support both file and stdin/stdout**
   - Allow reading from stdin when no input file is provided
   - Allow writing to stdout when no output file is specified

3. **Provide useful documentation**
   - Clear docstring with examples
   - Comprehensive man page
   - Meaningful help messages

4. **Handle errors gracefully**
   - Print error messages to stderr
   - Return appropriate exit codes
   - Provide helpful error messages

5. **JSON Support**
   - When appropriate, add JSON input/output options
   - Follow the pattern of existing tools

6. **Tool Documentation**
   - Create a README.md for tools that require configuration or have complex usage
   - Include the following sections in the README.md:
     - Overview
     - Setup and Configuration
     - Advanced Usage
     - Examples
     - Troubleshooting
   - This provides developers with important information that doesn't fit in man pages

7. **Environment Variables**
   - Use existing environment variables when possible
   - Important standard environment variables include:
     - `DTOOLKIT_REPO` - Path to the toolkit repository (essential for locating resources)
     - `DDATA` - Main data directory at ~/data
     - `DBACKUP` - Backup directory at ~/data/backup
     - `DREPOS` - Repository directory at ~/repos (symlinked to /data/repos)
     - `USER_NAME` - User's full name
     - `USER_EMAIL` - User's email address
     - `GITHUB_USERNAME` - User's GitHub username
   - Check for environment variables with `os.environ.get("VARIABLE_NAME")` with fallbacks
   - Document any required environment variables in both the man page and README.md

## Make Targets

Useful make commands for development:
- `make install` - Install/reinstall all tools (use after changes)
- `make check` - Run linting and type-checking
- `make test` - Run all tests
- `make clean` - Clean up generated files
- `make all` - Build and install everything

## Python Dependencies

- Add Python dependencies to `pyproject.toml`:
  ```toml
  dependencies = [
    "requests>=2.28.0",
    "beautifulsoup4>=4.11.0",
    "toml>=0.10.2",
    # Add new dependency here
  ]
  ```
- Run `make build` to sync dependencies