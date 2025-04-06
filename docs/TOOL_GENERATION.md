# Tool Generation Checklist

This document provides a structured checklist for AI assistants to follow when creating new utility tools for the scripts framework. Following this checklist ensures all tools are complete, well-documented, and follow the framework's conventions.

## 1. Initial Planning

- [ ] Understand the user's requirements for the tool
- [ ] Identify required inputs, outputs, and functionality
- [ ] Plan command-line options and interface
- [ ] Determine dependencies needed
- [ ] Check for existing similar tools to maintain consistency

## 2. Directory Structure

- [ ] Create tool directory in `/tools/{toolname}/`
- [ ] Create main script at `/tools/{toolname}/{toolname}.py`
- [ ] Create man page at `/tools/{toolname}/{toolname}.1`
- [ ] Create launcher script at `/bin/{toolname}`

## 3. Main Script Implementation

- [ ] Add proper shebang `#!/usr/bin/env python3`
- [ ] Write comprehensive docstring with description, usage, and examples
- [ ] Import necessary libraries
- [ ] Implement argument parsing with argparse
- [ ] Handle stdin input when no arguments provided
- [ ] Add `--version` and `--help` options
- [ ] Implement main function with proper error handling
- [ ] Add JSON output option when appropriate
- [ ] Handle both piped input and direct argument input
- [ ] Ensure script exits with appropriate status codes

## 4. Launcher Script Implementation

- [ ] Add proper shebang `#!/usr/bin/env bash`
- [ ] Implement robust symlink resolution
- [ ] Add fallback path searching for tool directory
- [ ] Add `--debug` option for path troubleshooting
- [ ] Add `--man` handler to display man page
- [ ] Add `--version` handler
- [ ] Include error handling for missing scripts
- [ ] Use UV for dependency management
- [ ] Pass all arguments to the main script

## 5. Man Page Creation

- [ ] Include proper `.TH` header with tool name and date
- [ ] Add NAME section with brief description
- [ ] Add SYNOPSIS section showing usage pattern
- [ ] Add DESCRIPTION with comprehensive explanation
- [ ] Document all OPTIONS with clear descriptions
- [ ] Include EXAMPLES section with practical usage examples
- [ ] Add ENVIRONMENT section if environment variables are used
- [ ] Add FILES section if configuration files are used
- [ ] Document EXIT STATUS codes
- [ ] Add SEE ALSO section with related commands

## 6. Test Implementation

- [ ] Create test file at `/tests/test_{toolname}.py`
- [ ] Write unit tests for core functionality
- [ ] Mock external dependencies in tests
- [ ] Test with various input types (stdin, arguments)
- [ ] Test error handling and edge cases
- [ ] Test command-line option parsing

## 7. Configuration

- [ ] Update `pyproject.toml` with any new dependencies
- [ ] Create setup script for tool if needed (e.g., API key setup)
- [ ] Make all scripts executable with `chmod +x`

## 8. Documentation

- [ ] Ensure docstrings are comprehensive
- [ ] Make sure help output is clear and useful
- [ ] Add examples in man page that cover common use cases
- [ ] Document environment variables and config files

## 9. Finalization

- [ ] Run tests to verify functionality
- [ ] Update setup-links.sh if necessary
- [ ] Run setup-links.sh to create symlinks
- [ ] Test symlinked version of the tool
- [ ] Verify `--help`, `--man`, and `--version` work correctly

## Example Tool Structure

```
/scripts/
├── bin/
│   └── toolname               # Launcher script
├── tools/
│   └── toolname/
│       ├── toolname.py        # Main implementation
│       └── toolname.1         # Man page
├── tests/
│   └── test_toolname.py       # Unit tests
└── pyproject.toml             # Updated with dependencies
```

## Tips for Robust Implementation

1. **Error Handling**: Always handle errors gracefully with clear error messages
2. **Symlink Resolution**: Use the standard symlink resolution code to ensure tools work when symlinked
3. **Stdin Handling**: Always support both direct arguments and stdin for maximum flexibility
4. **Help Documentation**: Include comprehensive help output and man pages
5. **JSON Support**: When appropriate, add JSON output options for programmatic use
6. **Testing**: Mock external dependencies for reliable testing
7. **Consistent Naming**: Follow the naming conventions of existing tools
8. **Exit Codes**: Use standard exit codes (0 for success, non-zero for failure)