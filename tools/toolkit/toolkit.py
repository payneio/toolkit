#!/usr/bin/env python3
"""
toolkit: Manage and display information about toolkit utilities

Toolkit helps you discover and work with the available utilities in your toolkit.

Usage: toolkit [command] [options]

Examples:
  toolkit                  # Show help information
  toolkit list             # List all available tools
  toolkit list --json      # List all available tools in JSON format
  toolkit info docx2md     # Show detailed information about a specific tool
  toolkit info docx2md --json  # Show detailed information in JSON format
  toolkit create newtool   # Create a new tool in its own category
  toolkit create xlsx2md --category document  # Add tool to existing category
"""

import sys
import os
import json
import argparse
import glob
import yaml
from pathlib import Path
import re


def parse_frontmatter(md_path):
    """Parse YAML frontmatter from a markdown file"""
    try:
        with open(md_path, "r") as f:
            content = f.read()

        # Check for frontmatter
        if not content.startswith("---\n"):
            return None

        # Find the closing ---
        end_match = content.find("\n---\n", 4)
        if end_match == -1:
            return None

        # Extract and parse YAML
        frontmatter = content[4:end_match]
        return yaml.safe_load(frontmatter)

    except Exception as e:
        print(f"Error parsing frontmatter in {md_path}: {e}", file=sys.stderr)
        return None


def get_tools_info():
    """Get information about all tools from their markdown frontmatter"""
    # Find the toolkit directory (parent of the directory containing this script)
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    toolkit_dir = os.path.dirname(os.path.dirname(script_dir))
    tools_dir = os.path.join(toolkit_dir, "tools")
    tools = []

    # Find all markdown files in tools subdirectories
    for md_file in glob.glob(os.path.join(tools_dir, "**", "*.md"), recursive=True):
        # Skip README files and files in test directories
        if os.path.basename(md_file) == "README.md" or "/tests/" in md_file:
            continue

        # Parse frontmatter
        metadata = parse_frontmatter(md_file)

        if metadata and "command" in metadata and "description" in metadata:
            tools.append(
                {
                    "command": metadata["command"],
                    "description": metadata["description"],
                    "category": metadata.get("category", "unknown"),
                    "version": metadata.get("version", "1.0.0"),
                    "system_dependencies": metadata.get("system_dependencies", []),
                    "script": metadata.get("script", ""),
                }
            )

    return sorted(tools, key=lambda x: x["command"])


def print_tool_list(tools, verbose=False):
    """Print a formatted list of tools"""
    # Group tools by category
    by_category = {}
    for tool in tools:
        category = tool["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool)

    # Output formatted information
    print("Toolkit Utilities")
    print("================\n")

    for category, category_tools in sorted(by_category.items()):
        print(f"{category.capitalize()} Tools:")
        print("-" * (len(category) + 7))

        for tool in category_tools:
            print(f"  {tool['command']:<15} - {tool['description']}")

            if verbose:
                if tool.get("system_dependencies"):
                    deps = ", ".join(tool["system_dependencies"])
                    print(f"    Dependencies: {deps}")
                print(f"    Version: {tool['version']}")
                print()

        print()


def print_tool_info(tool_name, tools):
    """Print detailed information about a specific tool"""
    tool = next((t for t in tools if t["command"] == tool_name), None)

    if not tool:
        print(f"Error: Tool '{tool_name}' not found")
        return 1

    print(f"{tool['command']} - {tool['description']}")
    print("=" * 70)
    print(f"Category: {tool['category']}")
    print(f"Version: {tool['version']}")
    if tool.get("system_dependencies"):
        deps = ", ".join(tool["system_dependencies"])
        print(f"System Dependencies: {deps}")
    print("=" * 70)

    # Try to find and display the markdown documentation
    # Go up three directories from toolkit.py: toolkit.py -> toolkit/ -> tools/ -> root/
    toolkit_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )
    md_path = os.path.join(
        toolkit_root,
        "tools",
        tool["category"],
        f"{tool['command']}.md",
    )

    if os.path.exists(md_path):
        try:
            with open(md_path, "r") as f:
                content = f.read()

                # Skip frontmatter and get documentation content
                if content.startswith("---\n"):
                    end_match = content.find("\n---\n", 4)
                    if end_match != -1:
                        # Extract content after frontmatter
                        doc_content = content[end_match + 5 :].strip()
                        if doc_content:
                            print("\n")
                            print(doc_content)
        except Exception as e:
            print(f"Error reading markdown file: {e}", file=sys.stderr)

    return 0


def print_tool_info_json(tool_name, tools):
    """Return detailed information about a specific tool in JSON format"""
    tool = next((t for t in tools if t["command"] == tool_name), None)

    if not tool:
        print(json.dumps({"error": f"Tool '{tool_name}' not found"}), file=sys.stderr)
        return 1

    print(json.dumps(tool, indent=2))
    return 0


def get_toolkit_root():
    """Find the toolkit root directory"""
    # First try environment variable
    env_path = os.environ.get("TOOLKIT_REPO_PATH")
    if env_path:
        toolkit_root = Path(env_path).resolve()
        if not (toolkit_root / "pyproject.toml").exists():
            print(
                f"Error: TOOLKIT_REPO_PATH is set to '{env_path}' but pyproject.toml not found there.",
                file=sys.stderr,
            )
            sys.exit(1)
        return toolkit_root

    # Fall back to script location (editable install)
    script_path = Path(__file__).resolve()
    toolkit_root = script_path.parent.parent.parent

    # Verify we found a valid toolkit repo
    if not (toolkit_root / "pyproject.toml").exists():
        print("Error: Could not find toolkit repository.", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "Set the TOOLKIT_REPO_PATH environment variable to your toolkit directory:",
            file=sys.stderr,
        )
        print("  export TOOLKIT_REPO_PATH=/path/to/toolkit", file=sys.stderr)
        print("", file=sys.stderr)
        print("Or run the command from within the toolkit repository.", file=sys.stderr)
        sys.exit(1)

    return toolkit_root


def create_tool(name, category=None, description="A simple utility"):
    """Create a new tool with proper structure"""

    # Validate tool name
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(f"Error: Tool name '{name}' is invalid.", file=sys.stderr)
        print(
            "Tool names must start with a letter and contain only lowercase letters, numbers, and underscores.",
            file=sys.stderr,
        )
        return 1

    if "-" in name:
        print(f"Error: Tool name '{name}' contains hyphens.", file=sys.stderr)
        print("Use underscores instead of hyphens in tool names.", file=sys.stderr)
        return 1

    toolkit_root = get_toolkit_root()
    tools_dir = toolkit_root / "tools"

    # Determine category and paths
    if category:
        tool_dir = tools_dir / category
        if not tool_dir.exists():
            print(f"Error: Category '{category}' does not exist.", file=sys.stderr)
            print(
                f"Available categories: {', '.join(sorted([d.name for d in tools_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]))}",
                file=sys.stderr,
            )
            return 1
        module_path = f"tools.{category}.{name}"
    else:
        category = name
        tool_dir = tools_dir / name
        tool_dir.mkdir(exist_ok=True)
        module_path = f"tools.{name}.{name}"

    print(f"Creating new tool: {name} in category: {category}")

    # Create __init__.py if it doesn't exist
    init_file = tool_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Created {init_file.relative_to(toolkit_root)}")

    # Create Python script
    script_file = tool_dir / f"{name}.py"
    if script_file.exists():
        print(
            f"Error: {script_file.relative_to(toolkit_root)} already exists!",
            file=sys.stderr,
        )
        return 1

    script_template = f'''#!/usr/bin/env python3
"""
{name}: {description}

Usage: {name} [options]
"""
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="{description}")
    parser.add_argument("--version", action="version", version="{name} 1.0.0")
    args = parser.parse_args()

    # Your code here
    print("Hello from {name}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

    script_file.write_text(script_template)
    script_file.chmod(0o755)
    print(f"Created {script_file.relative_to(toolkit_root)}")

    # Create markdown documentation with frontmatter
    md_file = tool_dir / f"{name}.md"
    if md_file.exists():
        print(
            f"Warning: {md_file.relative_to(toolkit_root)} already exists!",
            file=sys.stderr,
        )
    else:
        # Prepare frontmatter metadata
        metadata = {
            "command": name,
            "script": f"{category}/{name}.py",
            "description": description,
            "version": "1.0.0",
            "category": category,
        }

        # Generate markdown with frontmatter
        frontmatter = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        md_content = f"""---
{frontmatter}---

# {name}

{description}

## Installation

```bash
cd /path/to/toolkit
make install
which {name}
```

## Usage

```bash
{name} [options]
```

### Options

```bash
{name} [options]

Options:
  -h, --help          Show help message
```

## Examples

```bash
# Example usage
{name}
```

## Features

- Feature 1
- Feature 2
- Feature 3
"""

        md_file.write_text(md_content)
        print(f"Created {md_file.relative_to(toolkit_root)}")

    # Update pyproject.toml
    pyproject_file = toolkit_root / "pyproject.toml"
    pyproject_updated = update_pyproject(pyproject_file, name, module_path)

    if pyproject_updated:
        print(f"Updated {pyproject_file.relative_to(toolkit_root)}")

    print()
    print("✓ Tool created successfully!")
    print()
    print("Next steps:")
    print(f"  1. Edit the implementation: {script_file.relative_to(toolkit_root)}")
    print(f"  2. Update documentation: {md_file.relative_to(toolkit_root)}")

    if not pyproject_updated:
        print(f'  3. Add to pyproject.toml: {name} = "{module_path}:main"')
        print(f"  4. Install: cd {toolkit_root} && uv tool install --editable .")
        print(f"  5. Test: {name} --help")
    else:
        print(
            f"  3. Install: cd {toolkit_root} && uv tool install --reinstall --editable ."
        )
        print(f"  4. Test: {name} --help")

    print()
    print(f"The tool will be available as '{name}' command after installation.")

    return 0


def update_pyproject(pyproject_file, tool_name, module_path):
    """Add tool entry to pyproject.toml [project.scripts] section"""
    try:
        with open(pyproject_file, "r") as f:
            content = f.read()

        # Find [project.scripts] section
        scripts_match = re.search(
            r"(\[project\.scripts\].*?)(?=\n\[|\Z)", content, re.DOTALL
        )
        if not scripts_match:
            return False

        scripts_section = scripts_match.group(1)

        # Check if tool already exists
        if re.search(rf"^{re.escape(tool_name)}\s*=", scripts_section, re.MULTILINE):
            print(f"Warning: Entry for '{tool_name}' already exists in pyproject.toml")
            return False

        # Determine which category to add to based on module path
        category_map = {
            "tools.document": "# Document conversion tools",
            "tools.search": "# Search and indexing tools",
            "tools.gpt": "# AI and automation tools",
            "tools.browser": "# AI and automation tools",
            "tools.mdscraper": "# AI and automation tools",
            "tools.email": "# Email tools",
            "tools.system": "# System tools",
            "tools.android": "# Android tools",
            "tools.toolkit": "# Toolkit management",
        }

        # Find the appropriate category
        category_prefix = ".".join(module_path.split(".")[:2])
        category_comment = category_map.get(category_prefix, "# Other tools")

        # If category doesn't exist in the map, add it at the end
        if category_prefix not in category_map:
            # Add new category section before toolkit management
            toolkit_pos = content.find("# Toolkit management")
            if toolkit_pos != -1:
                new_entry = (
                    f'\n{category_comment}\n{tool_name} = "{module_path}:main"\n'
                )
                content = (
                    content[:toolkit_pos] + new_entry + "\n" + content[toolkit_pos:]
                )
            else:
                # Just append at the end of [project.scripts]
                scripts_end = scripts_match.end()
                new_entry = (
                    f'\n{category_comment}\n{tool_name} = "{module_path}:main"\n'
                )
                content = content[:scripts_end] + new_entry + content[scripts_end:]
        else:
            # Find the category comment and add after it
            category_pos = content.find(category_comment)
            if category_pos != -1:
                # Find the end of this category (next comment or end of section)
                section_start = category_pos
                next_comment = content.find(
                    "\n#", section_start + len(category_comment)
                )
                if next_comment == -1 or next_comment > scripts_match.end():
                    next_comment = scripts_match.end()

                # Find the last non-empty line in this category
                section_content = content[section_start:next_comment]
                lines = section_content.split("\n")

                # Find where to insert (after last tool entry in category)
                insert_pos = section_start + len(category_comment)
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() and not line.strip().startswith("#"):
                        insert_pos = section_start + sum(
                            len(line_) + 1 for line_ in lines[: i + 1]
                        )

                new_entry = f'\n{tool_name} = "{module_path}:main"'
                content = content[:insert_pos] + new_entry + content[insert_pos:]

        # Write back
        with open(pyproject_file, "w") as f:
            f.write(content)

        return True

    except Exception as e:
        print(
            f"Warning: Could not automatically update pyproject.toml: {e}",
            file=sys.stderr,
        )
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Manage and display information about toolkit utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]
        if __doc__
        else "",  # Use the docstring as extended help
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command", help="Command to execute", required=False
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all available tools")
    list_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose information"
    )
    list_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # Info command
    info_parser = subparsers.add_parser(
        "info", help="Show detailed information about a specific tool"
    )
    info_parser.add_argument("tool", help="Tool name")
    info_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new tool")
    create_parser.add_argument(
        "name", help="Tool name (lowercase letters, numbers, and underscores only)"
    )
    create_parser.add_argument(
        "--category",
        "-c",
        help="Add tool to existing category (e.g., document, search)",
    )
    create_parser.add_argument(
        "--description", "-d", default="A simple utility", help="Tool description"
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose information"
    )
    parser.add_argument("--version", action="version", version="toolkit 1.0.0")

    args = parser.parse_args()

    # Process based on command
    if args.command == "create":
        return create_tool(args.name, args.category, args.description)

    tools = get_tools_info()

    if args.command == "info":
        if getattr(args, "json", False):
            return print_tool_info_json(args.tool, tools)
        else:
            return print_tool_info(args.tool, tools)

    # Default to list if no command or explicit 'list' command
    if args.command is None or args.command == "list":
        if getattr(args, "json", False):
            # Output all tools in JSON format
            json.dump(tools, sys.stdout, indent=2)
            print()  # Add newline
        else:
            print_tool_list(tools, getattr(args, "verbose", False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
