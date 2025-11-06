#!/usr/bin/env python3
"""
md2pdf: Convert Markdown files to PDF

Converts Markdown files to PDF format with nice rendering of headers, lists,
code blocks, and other markdown elements. The tool uses pandoc with LaTeX
for high-quality PDF output.

The conversion process preserves markdown formatting and applies professional
styling including proper spacing, font choices, and page layout.

Usage: md2pdf file.md
       md2pdf -o output.pdf file.md
       cat file.md | md2pdf -o output.pdf
       md2pdf file.md  # Creates file.pdf in the same directory

Options:
  -o, --output FILE    Write PDF to FILE instead of <input_basename>.pdf
  --toc                Include table of contents
  --margin SIZE        Set page margins (default: 1in). Examples: 1in, 2cm, 20mm
  --font-size SIZE     Set base font size (default: 11pt). Examples: 10pt, 12pt
"""
import sys
import os
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown files to PDF")
    parser.add_argument('input_file', nargs='?', help="Input Markdown file (or read from stdin)")
    parser.add_argument('-o', '--output', help="Output PDF file (default: <input_basename>.pdf)")
    parser.add_argument('--toc', action='store_true', help="Include table of contents")
    parser.add_argument('--margin', default='1in', help="Page margins (default: 1in)")
    parser.add_argument('--font-size', default='11pt', help="Base font size (default: 11pt)")
    args = parser.parse_args()

    # Determine input source.
    if args.input_file:
        input_file = args.input_file
        if not os.path.isfile(input_file):
            print(f"Error: File '{input_file}' not found", file=sys.stderr)
            return 1

        if args.output:
            output_file = args.output
        else:
            basename = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"{basename}.pdf"
    else:
        # Reading from stdin
        if not args.output:
            print("Error: When reading from stdin, you must specify an output file with -o", file=sys.stderr)
            return 1
        input_file = None
        output_file = args.output

    try:
        # Build pandoc command with options for nice PDF rendering.
        pandoc_command = ["pandoc"]

        if input_file:
            pandoc_command.append(input_file)
        else:
            pandoc_command.append("-")  # Read from stdin

        pandoc_command.extend([
            "-f", "markdown",
            "-t", "pdf",
            "-o", output_file,
            "--pdf-engine=pdflatex",
            f"-V", f"geometry:margin={args.margin}",
            f"-V", f"fontsize={args.font_size}",
            "-V", "colorlinks=true",
            "-V", "linkcolor=blue",
            "-V", "urlcolor=blue",
        ])

        # Add table of contents if requested.
        if args.toc:
            pandoc_command.append("--toc")
            pandoc_command.extend(["--toc-depth", "3"])

        # Run pandoc conversion.
        result = subprocess.run(
            pandoc_command,
            check=True,
            capture_output=True,
            text=True,
            input=None if input_file else sys.stdin.read()
        )

        # Print success message to stderr.
        print(f"Created '{output_file}'", file=sys.stderr)

        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("Error: pandoc is not installed. Please install it with 'apt install pandoc texlive-latex-base'", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
