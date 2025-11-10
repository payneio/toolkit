#!/usr/bin/env python3
"""
text-extractor: Extract content and metadata from text files

Reads a text file and outputs a JSON object containing the file's content
and metadata including filename, size, creation and modification times.

Usage: text-extractor [options] [FILE]

Examples:
  text-extractor document.txt           # Extract from a text file
  cat file.txt | text-extractor         # Read from stdin
"""

import sys
import os
import json
import argparse
from datetime import datetime
import mimetypes
from pathlib import Path


def get_file_metadata(file_path):
    """Get file metadata including creation time, modification time, size, etc."""
    path = Path(file_path)
    stat = path.stat()

    # Get file modification and creation times
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
    try:
        ctime = datetime.fromtimestamp(stat.st_ctime).isoformat()
    except Exception:
        ctime = mtime  # Fallback if creation time not available

    # Get mime type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "text/plain"  # Default to plain text

    return {
        "filename": path.name,
        "path": str(path.absolute()),
        "size": stat.st_size,
        "created_at": ctime,
        "modified_at": mtime,
        "mime_type": mime_type,
        "extension": path.suffix.lstrip(".") if path.suffix else "",
    }


def process_file(file_path):
    """Extract content and metadata from the file."""
    # Get file metadata
    if file_path and os.path.exists(file_path):
        metadata = get_file_metadata(file_path)

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try again with latin-1 encoding
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
    else:
        # Reading from stdin
        content = sys.stdin.read()
        metadata = {
            "filename": "stdin",
            "path": "stdin",
            "size": len(content),
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "mime_type": "text/plain",
            "extension": "",
        }

    # Create result object
    result = {
        **metadata,
        "content": content,
        "title": metadata["filename"],
        "tags": [],  # No tags by default
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract content and metadata from text files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]
        if __doc__
        else "",  # Use the docstring as extended help
    )
    parser.add_argument("file", nargs="?", help="Input file (default: stdin)")
    parser.add_argument(
        "-v", "--version", action="version", version="text-extractor 1.0.0"
    )
    args = parser.parse_args()

    try:
        # Process the file
        result = process_file(args.file)

        # Output the result as JSON
        print(json.dumps(result, indent=2))

        return 0
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
