#!/usr/bin/env python3
"""
docx2md: Convert Word .docx files to Markdown
Usage: docx2md [file.docx]
"""
import sys
import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Convert Word .docx files to Markdown")
    parser.add_argument('input_file', help="Input .docx file")
    args = parser.parse_args()
    
    if not args.input_file.endswith('.docx'):
        print(f"Error: Input file must be a .docx file", file=sys.stderr)
        return 1
    
    input_file = args.input_file
    basename = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{basename}.md"
    
    try:
        # Convert using pandoc
        result = subprocess.run(
            ["pandoc", input_file, "-f", "docx", "-t", "markdown", "-o", output_file, "--extract-media=./media"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Converted '{input_file}' to '{output_file}'")
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
