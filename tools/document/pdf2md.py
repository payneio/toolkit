#!/usr/bin/env python3
"""
pdf2md: Convert PDF files to Markdown

Converts PDF files to Markdown format and writes the result to a file with
the same basename but .md extension. Also creates a directory for extracted
media assets named <basename>_media/. The markdown content is also sent to stdout.

The conversion process uses poppler-utils (pdftotext and pdfimages) to extract
text and images from the PDF, then uses pandoc to convert the text to Markdown.
The output preserves as much of the original layout as possible.

Usage: pdf2md file.pdf
       pdf2md -o output.md file.pdf
       pdf2md -m custom_media_dir file.pdf
       pdf2md -o output.md -m custom_media_dir file.pdf
       pdf2md file.pdf > another_file.md

Options:
  -o, --output FILE    Write markdown to FILE instead of <input_basename>.md
  -m, --media-dir DIR  Store extracted media files in DIR instead of <basename>_media
"""

import sys
import os
import re
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown")
    parser.add_argument("input_file", help="Input PDF file")
    parser.add_argument(
        "-o", "--output", help="Output markdown file (default: <input_basename>.md)"
    )
    parser.add_argument(
        "-m",
        "--media-dir",
        help="Directory for extracted media files (default: <basename>_media)",
    )
    args = parser.parse_args()

    if not args.input_file.endswith(".pdf"):
        print("Error: Input file must be a PDF file", file=sys.stderr)
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

    # Create media directory if it doesn't exist
    os.makedirs(media_dir, exist_ok=True)

    try:
        # Create a temporary directory for conversion
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # First use pdftotext (from poppler-utils) to extract text
            temp_txt = os.path.join(temp_dir, "temp_content.txt")
            # Use pdftotext with -nopgbrk to avoid page breaks that can mess up tables
            subprocess.run(
                ["pdftotext", "-nopgbrk", input_file, temp_txt],
                check=True,
                capture_output=True,
                text=True,
            )

            # Process the text file to clean up formatting issues
            with open(temp_txt, "r") as f:
                content = f.read()

            # Remove common footer patterns
            content = re.sub(
                r"(?m)^\s*\d+\s+The Social Issues Research Centre.*$", "", content
            )

            # Replace excessive spaces with reasonable indentation
            content = re.sub(r"(?m)^(\s{6,})", "  ", content)

            # Clean up empty lines
            content = re.sub(r"\n{3,}", "\n\n", content)

            # Write cleaned content back to file
            with open(temp_txt, "w") as f:
                f.write(content)

            # Extract images using pdfimages
            subprocess.run(
                ["pdfimages", "-j", input_file, os.path.join(media_dir, "image")],
                check=True,
                capture_output=True,
                text=True,
            )

            # Then convert text to Markdown using pandoc with table support
            result = subprocess.run(
                [
                    "pandoc",
                    temp_txt,
                    "-f",
                    "markdown+simple_tables+table_captions+yaml_metadata_block",
                    "-t",
                    "markdown_github",
                    "--wrap=none",
                    "--standalone",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Process the markdown to further clean it up
            markdown = result.stdout

            # Fix table formatting if needed
            markdown = re.sub(r"\|-+\|\n\|-+\|", "", markdown)

        # Write markdown to file
        with open(output_file, "w") as f:
            f.write(markdown)

        # Also output to stdout
        print(markdown)

        # Print message to stderr about file creation
        print(
            f"Created '{output_file}' with media in '{media_dir}'"
            + ("" if media_dir.endswith("/") else "/"),
            file=sys.stderr,
        )

        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        if "pdftohtml" in str(e):
            print(
                "Error: pdftohtml is not installed. Please install it with 'apt install poppler-utils'",
                file=sys.stderr,
            )
        else:
            print(
                "Error: pandoc is not installed. Please install it with 'apt install pandoc'",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    sys.exit(main())
