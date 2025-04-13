#!/usr/bin/env python3
"""
docx2md: Convert Word .docx files to CommonMark

Converts Word .docx files to CommonMark format (a standardized Markdown specification)
and writes the result to a file with the same basename but .md extension. Also creates 
a directory for extracted media assets named <basename>_media/. The markdown content is
also sent to stdout.

This tool uses pandoc with the CommonMark output format, which produces clean, 
standardized markdown with the following properties:
  - Standards-compliant, well-formed markdown
  - Consistent rendering across different Markdown implementations
  - Proper spacing of list items and headings
  - Clean table formatting
  - No line wrapping for easier editing

Usage: docx2md file.docx
       docx2md -o output.md file.docx
       docx2md file.docx > another_file.md
       docx2md --no-format file.docx

Options:
  -o, --output FILE    Write markdown to FILE instead of <input_basename>.md
  -m, --media-dir DIR  Store extracted media files in DIR instead of <basename>_media
  --no-format          Disable additional markdown formatting fixes (rarely needed with CommonMark)
"""
import sys
import os
import subprocess
import argparse
import re

def fix_markdown_formatting(markdown_text):
    """
    Apply minimal formatting fixes if needed.
    
    With CommonMark format, most formatting issues should already be resolved,
    but this function remains for rare cases where additional fixes might be needed.
    """
    # Ensure trailing newline
    if not markdown_text.endswith('\n'):
        markdown_text += '\n'
    
    # Minimal formatting fixes for edge cases
    # 1. Ensure headings have blank lines after them if missing
    lines = markdown_text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        result.append(line)
        
        # Check if this is a heading and needs a blank line after it
        if (re.match(r'^#+\s+', line.strip()) and 
            i < len(lines) - 1 and lines[i+1].strip() and 
            not lines[i+1].startswith('#')):
            # Add a blank line after the heading if not already present
            result.append('')
    
    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(description="Convert Word .docx files to Markdown")
    parser.add_argument('input_file', help="Input .docx file")
    parser.add_argument('-o', '--output', help="Output markdown file (default: <input_basename>.md)")
    parser.add_argument('-m', '--media-dir', help="Directory for extracted media files (default: <basename>_media)")
    parser.add_argument('--no-format', action='store_true', help="Disable markdown formatting fixes")
    args = parser.parse_args()
    
    if not args.input_file.endswith('.docx'):
        print("Error: Input file must be a .docx file", file=sys.stderr)
        return 1
    
    input_file = args.input_file
    
    if args.output:
        output_file = args.output
        # Extract the basename from the output file for media directory name
        media_basename = os.path.splitext(os.path.basename(output_file))[0]
    else:
        basename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{basename}.md"
        media_basename = basename
    
    # Set media directory
    if args.media_dir:
        media_dir = args.media_dir
    else:
        media_dir = f"{media_basename}_media"
    
    try:
        # Convert using pandoc with media extraction and CommonMark format
        pandoc_command = [
            "pandoc", 
            input_file, 
            "-f", "docx", 
            # Use CommonMark format for standardized, clean output
            "-t", "commonmark",
            # Don't wrap lines
            "--wrap=none",
            # Extract media
            f"--extract-media={media_dir}"
        ]
        
        result = subprocess.run(
            pandoc_command,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Apply markdown formatting fixes if not disabled
        if args.no_format:
            markdown_content = result.stdout
        else:
            markdown_content = fix_markdown_formatting(result.stdout)
        
        # Write markdown to file
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        
        # Also output to stdout
        print(markdown_content)
        
        # Print message to stderr about file creation
        print(f"Created '{output_file}' with media in '{media_dir}'"+("" if media_dir.endswith("/") else "/"), file=sys.stderr)
        
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("Error: pandoc is not installed. Please install it with 'apt install pandoc'", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
