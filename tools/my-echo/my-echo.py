#!/usr/bin/env python3
"""
my-echo: A simple echo utility

A flexible echo tool that can process text or JSON input
and apply transformations like converting to uppercase.

Usage: my-echo [options] [message]

Examples:
  my-echo "Hello, world"            # Basic usage
  my-echo -u "Hello, world"         # Convert to uppercase
  my-echo -j '{"name":"John"}'      # Process JSON input
  cat file.json | my-echo -j        # Read JSON from stdin
  my-echo -j -u '{"key":"value"}'   # Parse JSON and uppercase string values
"""
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Echo a message with optional transformations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    parser.add_argument('message', nargs='?', help="Message to echo (default: reads from stdin)")
    parser.add_argument('-u', '--uppercase', action='store_true', help="Convert to uppercase")
    parser.add_argument('-j', '--json', action='store_true', help="Parse input as JSON")
    parser.add_argument('-v', '--version', action='version', version='my-echo 1.0.0')
    args = parser.parse_args()
    
    # Read from stdin or argument
    if args.message:
        data = args.message
    else:
        data = sys.stdin.read().strip()
    
    # Process data
    if args.json:
        try:
            data = json.loads(data)
            result = {"echo": data}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input - {str(e)}", file=sys.stderr)
            return 1
    else:
        result = data
        
    if args.uppercase:
        if args.json:
            # Convert string values in JSON to uppercase
            if isinstance(result["echo"], str):
                result["echo"] = result["echo"].upper()
            elif isinstance(result["echo"], dict):
                for key, value in result["echo"].items():
                    if isinstance(value, str):
                        result["echo"][key] = value.upper()
        else:
            result = result.upper()
        
    # Output results
    if args.json:
        json.dump(result, sys.stdout)
    else:
        print(result)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
