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
"""
import sys
import os
import json
import argparse
import glob
import toml

def get_tools_info():
    """Get information about all tools from their tools.toml files"""
    # Find the toolkit directory (parent of the directory containing this script)
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    toolkit_dir = os.path.dirname(os.path.dirname(script_dir))
    tools_dir = os.path.join(toolkit_dir, "tools")
    tools = []
    
    for toml_file in glob.glob(os.path.join(tools_dir, "**", "tools.toml"), recursive=True):
        category = os.path.basename(os.path.dirname(toml_file))
        try:
            data = toml.load(toml_file)
            
            # Handle single tool or list of tools
            tool_data = data.get("tool", [])
            if not isinstance(tool_data, list):
                tool_data = [tool_data]
                
            for tool in tool_data:
                if isinstance(tool, dict) and "command" in tool and "description" in tool:
                    tools.append({
                        "command": tool["command"],
                        "description": tool["description"],
                        "category": category,
                        "version": tool.get("version", "1.0.0"),
                        "system_dependencies": tool.get("system_dependencies", []),
                        "script": tool.get("script", "")
                    })
        except Exception as e:
            print(f"Error loading {toml_file}: {e}", file=sys.stderr)
    
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
    print("=" * (len(tool['command']) + len(tool['description']) + 3))
    print(f"Category: {tool['category']}")
    print(f"Version: {tool['version']}")
    
    if tool.get("system_dependencies"):
        deps = ", ".join(tool["system_dependencies"])
        print(f"System Dependencies: {deps}")
    
    # Try to find and display the script's docstring
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 
                               "tools", tool["category"], os.path.basename(tool["script"]))
    
    if os.path.exists(script_path):
        try:
            with open(script_path, 'r') as f:
                content = f.read()
                docstring_start = content.find('"""') + 3
                docstring_end = content.find('"""', docstring_start)
                if docstring_start > 2 and docstring_end > docstring_start:
                    docstring = content[docstring_start:docstring_end].strip()
                    print("\nHelp:")
                    print(docstring)
        except Exception as e:
            print(f"Error reading script file: {e}", file=sys.stderr)
    
    return 0

def print_tool_info_json(tool_name, tools):
    """Return detailed information about a specific tool in JSON format"""
    tool = next((t for t in tools if t["command"] == tool_name), None)
    
    if not tool:
        print(json.dumps({"error": f"Tool '{tool_name}' not found"}), file=sys.stderr)
        return 1
    
    print(json.dumps(tool, indent=2))
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Manage and display information about toolkit utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute', required=False)
    
    # List command
    list_parser = subparsers.add_parser('list', help="List all available tools")
    list_parser.add_argument('-v', '--verbose', action='store_true', help="Show verbose information")
    list_parser.add_argument('--json', action='store_true', help="Output in JSON format")
    
    # Info command
    info_parser = subparsers.add_parser('info', help="Show detailed information about a specific tool")
    info_parser.add_argument('tool', help="Tool name")
    info_parser.add_argument('--json', action='store_true', help="Output in JSON format")
    
    # Global options
    parser.add_argument('-v', '--verbose', action='store_true', help="Show verbose information")
    parser.add_argument('--version', action='version', version='toolkit 1.0.0')
    
    args = parser.parse_args()
    tools = get_tools_info()
    
    # Process based on command
    if args.command == 'info':
        if getattr(args, 'json', False):
            return print_tool_info_json(args.tool, tools)
        else:
            return print_tool_info(args.tool, tools)
    
    # Default to list if no command or explicit 'list' command
    if args.command is None or args.command == 'list':
        if getattr(args, 'json', False):
            # Output all tools in JSON format
            json.dump(tools, sys.stdout, indent=2)
            print()  # Add newline
        else:
            print_tool_list(tools, getattr(args, 'verbose', False))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
