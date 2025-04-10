#!/usr/bin/env python3
"""
docx2md: Convert Word .docx files to Markdown

Converts Word .docx files to Markdown format and writes the result to a file with
the same basename but .md extension. Also creates a directory for extracted
media assets named <basename>_media/. The markdown content is also sent to stdout.

Usage: docx2md file.docx
       docx2md -o output.md file.docx
       docx2md file.docx > another_file.md

Options:
  -o, --output FILE    Write markdown to FILE instead of <input_basename>.md
  -m, --media-dir DIR  Store extracted media files in DIR instead of <basename>_media
"""
import sys
import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Convert Word .docx files to Markdown")
    parser.add_argument('input_file', help="Input .docx file")
    parser.add_argument('-o', '--output', help="Output markdown file (default: <input_basename>.md)")
    parser.add_argument('-m', '--media-dir', help="Directory for extracted media files (default: <basename>_media)")
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
        # Convert using pandoc with media extraction
        result = subprocess.run(
            ["pandoc", input_file, "-f", "docx", "-t", "markdown", f"--extract-media={media_dir}"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Write markdown to file
        with open(output_file, 'w') as f:
            f.write(result.stdout)
        
        # Also output to stdout
        print(result.stdout)
        
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
