# Toolkit Tool Creation Guide

This guide provides the essential steps and information needed to create a new tool for the toolkit framework.

## Quick Reference

1. **Check for existing tools**
   - Run `toolkit` to list existing tools
   - Check if similar functionality already exists
   - Determine appropriate category or create new one

2. **Choose a name and description**
   - Use kebab-case for command names (e.g., `word-count`)
   - Select category directory or create new one (e.g., `text`)
   - Craft a clear, concise description

3. **Create directory structure**
   - Make a category directory if needed: `mkdir -p tools/<category>`
   - Create tool-specific directory ONLY if needed for complex tools: `mkdir -p tools/<category>/<toolname>`

4. **Update category's tools.toml file**
   - Each category has ONE tools.toml file at `tools/<category>/tools.toml`
   - For multiple tools in a category, add each as a separate [tool] entry in the same file
   - Create the file if it doesn't exist or append to it if it does
   
   ```toml
   # First tool in the category
   [tool]
   command = "tool-name"
   script = "category/tool-name.py"
   description = "Clear description of what the tool does"
   version = "1.0.0"
   system_dependencies = ["optional-dependency"]
   
   # Second tool in the same category (if applicable)
   [tool]
   command = "another-tool"
   script = "category/another-tool.py"
   description = "Description of another tool"
   version = "1.0.0"
   system_dependencies = ["another-dependency"]
   ```

5. **Create Python script**
   - Create script at `tools/<category>/<tool-name>.py`
   - Follow script template below
   - Ensure script is executable: `chmod +x tools/<category>/<tool-name>.py`

6. **Documentation**
   - Create good docstrings and help text in the script
   - Documentation is provided through --help, not man pages

7. **Create README.md (optional but recommended)**
   - Create a README.md if the tool needs additional developer information
   - Include configuration details, API information, or advanced usage
   - Place at `tools/<category>/README.md` or `tools/<category>/<tool-name>/README.md`

8. **Generate bin launcher and install**
   - Run `make bin` to generate bin launcher
   - Run `make install` to install the tool

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

## Using the Make System

- `make new-tool name=toolname` - Create a new tool skeleton (alternative to manual creation)
- `make bin` - Generate bin launcher scripts
- `make man` - Generate man pages (will not overwrite existing man pages)
- `make install` - Install tools to ~/.local/bin and man pages
- `make all` - Run all necessary steps to build and install

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