#!/usr/bin/env python3
"""
html2text: Convert HTML content to plain text

Converts HTML content to readable plain text by removing HTML tags,
preserving basic structure, and formatting the content for terminal viewing.
Works well with email content.

Usage: html2text [options] [file]

Examples:
  html2text email.html        # Convert HTML file to text
  cat email.html | html2text  # Convert HTML from stdin to text
  protonmail read 42 | html2text  # Convert ProtonMail HTML email to text
"""

import sys
import argparse
import re
import html
from html.parser import HTMLParser
import textwrap


class HTMLToTextParser(HTMLParser):
    """HTML parser that converts HTML to readable plain text."""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False
        self.in_paragraph = False
        self.in_list_item = False
        self.in_anchor = False
        self.href = ""
        self.indent_level = 0
        self.list_item_num = 0
        self.in_header = False
        self.header_level = 0
        self.in_pre = False
        self.in_code = False
        self.buffer = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "head" or tag == "style" or tag == "script":
            self.skip = True
            return

        if tag == "p":
            if self.result and self.result[-1] != "":
                self.result.append("")
            self.in_paragraph = True
        elif tag == "br":
            self.result.append("")
        elif (
            tag == "h1"
            or tag == "h2"
            or tag == "h3"
            or tag == "h4"
            or tag == "h5"
            or tag == "h6"
        ):
            if self.result and self.result[-1] != "":
                self.result.append("")
            self.in_header = True
            self.header_level = int(tag[1])
        elif tag == "ul" or tag == "ol":
            self.result.append("")
            self.indent_level += 2
            if tag == "ol":
                self.list_item_num = 1
            else:
                self.list_item_num = 0
        elif tag == "li":
            self.in_list_item = True
            prefix = " " * self.indent_level
            if self.list_item_num > 0:
                prefix += f"{self.list_item_num}. "
                self.list_item_num += 1
            else:
                prefix += "• "
            self.buffer = prefix
        elif tag == "a" and "href" in attrs_dict:
            self.in_anchor = True
            self.href = attrs_dict["href"]
        elif tag == "pre":
            if self.result and self.result[-1] != "":
                self.result.append("")
            self.in_pre = True
        elif tag == "code":
            self.in_code = True
        elif tag == "div":
            if self.result and self.result[-1] != "":
                self.result.append("")
        elif tag == "blockquote":
            if self.result and self.result[-1] != "":
                self.result.append("")
            self.indent_level += 4
            self.result.append(" " * self.indent_level + "> ")
        elif tag == "hr":
            self.result.append("-" * 70)

    def handle_endtag(self, tag):
        if tag == "head" or tag == "style" or tag == "script":
            self.skip = False
            return

        if tag == "p":
            if self.result and self.buffer:
                self.result.append(self.buffer)
                self.buffer = ""
            self.in_paragraph = False
            self.result.append("")
        elif (
            tag == "h1"
            or tag == "h2"
            or tag == "h3"
            or tag == "h4"
            or tag == "h5"
            or tag == "h6"
        ):
            if self.buffer:
                self.result.append(self.buffer)
                underline = "=" if self.header_level <= 2 else "-"
                self.result.append(underline * len(self.buffer))
                self.buffer = ""
            self.in_header = False
            self.result.append("")
        elif tag == "ul" or tag == "ol":
            self.indent_level -= 2
            self.list_item_num = 0
            self.result.append("")
        elif tag == "li":
            if self.buffer:
                self.result.append(self.buffer)
                self.buffer = ""
            self.in_list_item = False
        elif tag == "a":
            if self.in_anchor and self.href and self.buffer:
                if self.href not in self.buffer:
                    self.buffer += f" [{self.href}]"
            self.in_anchor = False
        elif tag == "pre":
            self.in_pre = False
            self.result.append("")
        elif tag == "code":
            self.in_code = False
        elif tag == "blockquote":
            self.indent_level -= 4
            self.result.append("")

    def handle_data(self, data):
        if self.skip:
            return

        # Clean and normalize whitespace
        if not self.in_pre and not self.in_code:
            data = " ".join(data.split())

        if data.strip():
            if self.in_list_item or self.in_header:
                self.buffer += data
            elif self.in_paragraph:
                if self.buffer:
                    self.buffer += " " + data
                else:
                    self.buffer = data
            else:
                self.result.append(data)

    def handle_entityref(self, name):
        if self.skip:
            return

        # Convert HTML entities to their corresponding characters
        try:
            char = html.unescape(f"&{name};")
            if self.in_list_item or self.in_header or self.in_paragraph:
                self.buffer += char
            else:
                self.result.append(char)
        except Exception:
            pass

    def handle_charref(self, name):
        if self.skip:
            return

        # Convert character references to their corresponding characters
        try:
            char = html.unescape(f"&#{name};")
            if self.in_list_item or self.in_header or self.in_paragraph:
                self.buffer += char
            else:
                self.result.append(char)
        except Exception:
            pass

    def get_text(self):
        """Get the processed text with proper wrapping."""
        # Process any remaining buffer
        if self.buffer:
            self.result.append(self.buffer)

        # Join all lines, handling indentation properly
        result = []
        wrapper = textwrap.TextWrapper(width=80)

        i = 0
        while i < len(self.result):
            line = self.result[i]

            # Skip empty lines, but preserve paragraph breaks
            if not line:
                result.append("")
                i += 1
                continue

            # Check if it's a list item or indented text
            indent_match = re.match(r"^(\s+)(.*?)$", line)
            if indent_match:
                indent = indent_match.group(1)
                content = indent_match.group(2)

                if content.startswith("• ") or re.match(r"^\d+\.\s", content):
                    # It's a list item, preserve the marker and indent rest of the paragraph
                    marker = re.match(r"^([•\d]+\.?\s+)", content).group(1)
                    remaining = content[len(marker) :]

                    # Set up custom wrapper for indented text
                    custom_wrapper = textwrap.TextWrapper(
                        width=80,
                        initial_indent=indent + marker,
                        subsequent_indent=indent + " " * len(marker),
                    )

                    result.append(custom_wrapper.fill(remaining))
                else:
                    # Regular indented text
                    custom_wrapper = textwrap.TextWrapper(
                        width=80, initial_indent=indent, subsequent_indent=indent
                    )
                    result.append(custom_wrapper.fill(content))
            else:
                # Regular wrapped text for paragraphs
                result.append(wrapper.fill(line))

            i += 1

        # Clean up multiple consecutive empty lines
        clean_result = []
        prev_empty = False
        for line in result:
            if not line and prev_empty:
                continue
            clean_result.append(line)
            prev_empty = not line

        return "\n".join(clean_result)


def convert_html_to_text(html_content):
    """Convert HTML content to readable plain text."""
    parser = HTMLToTextParser()
    parser.feed(html_content)
    return parser.get_text()


def clean_up_text(text):
    """Clean up the text by removing excessive whitespace and line breaks."""
    # Replace multiple newlines with double newlines (for paragraph separation)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML content to plain text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1],
    )

    parser.add_argument("file", nargs="?", help="HTML file to convert (default: stdin)")
    parser.add_argument(
        "-w", "--width", type=int, default=80, help="Maximum line width (default: 80)"
    )
    parser.add_argument("-v", "--version", action="version", version="html2text 1.0.0")

    args = parser.parse_args()

    # Read from file or stdin
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            print(f"Error reading file: {str(e)}", file=sys.stderr)
            return 1
    else:
        html_content = sys.stdin.read()

    # Check if the content actually has HTML tags
    if "<" in html_content and ">" in html_content:
        # Convert HTML to text
        text = convert_html_to_text(html_content)
        text = clean_up_text(text)
        print(text)
    else:
        # Content doesn't have HTML tags, just print it as is
        print(html_content.strip())

    return 0


if __name__ == "__main__":
    sys.exit(main())
