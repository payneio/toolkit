#!/usr/bin/env python3
"""
docx-extractor: Extract content and metadata from Word .docx files

Reads a Word .docx file and outputs a JSON object containing the file's content
and metadata including filename, size, title, author, creation date, etc.

Usage: docx-extractor [options] [FILE]

Examples:
  docx-extractor document.docx           # Extract from a Word file
"""
import sys
import os
import json
import argparse
import subprocess
from datetime import datetime
import mimetypes
from pathlib import Path
import re

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
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # Default for .docx
    
    return {
        "filename": path.name,
        "path": str(path.absolute()),
        "size": stat.st_size,
        "created_at": ctime,
        "modified_at": mtime,
        "mime_type": mime_type,
        "extension": path.suffix.lstrip(".") if path.suffix else "docx"
    }

def extract_docx_metadata(file_path):
    """Extract metadata from a DOCX file using pandoc."""
    metadata = {}
    
    try:
        # Method 1: Try to extract metadata using pandoc's native metadata extraction
        # Convert to JSON to capture metadata fields like title, author, date, etc.
        result = subprocess.run(
            ["pandoc", "--standalone", "--to=json", file_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        try:
            # Parse the JSON output
            data = json.loads(result.stdout)
            
            # Extract metadata fields from the JSON structure
            if "meta" in data:
                meta = data["meta"]
                
                # Extract title
                if "title" in meta:
                    title_content = meta["title"].get("c", [])
                    if title_content:
                        # Title might be a complex structure, try to extract text
                        title_parts = []
                        for part in title_content:
                            if isinstance(part, dict) and "c" in part:
                                title_parts.append(part["c"])
                            elif isinstance(part, str):
                                title_parts.append(part)
                        if title_parts:
                            metadata["title"] = " ".join(title_parts)
                
                # Extract author
                if "author" in meta:
                    author_data = meta["author"]
                    if isinstance(author_data, list) and author_data:
                        if "c" in author_data[0]:
                            metadata["author"] = author_data[0]["c"]
                        else:
                            # Try to extract author from complex structures
                            authors = []
                            for author in author_data:
                                if isinstance(author, dict) and "c" in author:
                                    authors.append(author["c"])
                            if authors:
                                metadata["author"] = ", ".join(authors)
                
                # Extract date
                if "date" in meta:
                    date_content = meta["date"]
                    if isinstance(date_content, dict) and "c" in date_content:
                        metadata["date"] = date_content["c"]
                
                # Extract keywords/tags
                if "keywords" in meta:
                    keywords_data = meta["keywords"]
                    if isinstance(keywords_data, dict) and "c" in keywords_data:
                        metadata["keywords"] = keywords_data["c"]
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract title from first header if not found in metadata
        if "title" not in metadata:
            # Convert to markdown and look for the first header
            result = subprocess.run(
                ["pandoc", "-f", "docx", "-t", "markdown", file_path],
                check=True,
                capture_output=True,
                text=True
            )
            
            content = result.stdout.strip()
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()
        
        return metadata
    except subprocess.CalledProcessError:
        # Fall back to basic metadata if pandoc extraction fails
        return metadata
    except FileNotFoundError:
        sys.stderr.write("Warning: pandoc not found, metadata extraction limited\n")
        return metadata

def extract_docx_content(file_path):
    """Extract content from a DOCX file using pandoc."""
    try:
        # Use pandoc to convert DOCX to plain text
        result = subprocess.run(
            ["pandoc", "-f", "docx", "-t", "plain", file_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error extracting DOCX content: {e}\n")
        if e.stderr:
            sys.stderr.write(e.stderr)
        return ""
    except FileNotFoundError:
        sys.stderr.write("Error: pandoc is not installed. Please install it with 'apt install pandoc'\n")
        return ""

def process_file(file_path):
    """Extract content and metadata from the file."""
    # Check if input file exists
    if not file_path or not os.path.exists(file_path):
        sys.stderr.write(f"Error: File '{file_path}' not found.\n")
        return {}
        
    # Get file metadata
    metadata = get_file_metadata(file_path)
    
    # Extract document metadata
    docx_metadata = extract_docx_metadata(file_path)
    
    # Extract content
    content = extract_docx_content(file_path)
    
    # Try to extract tags
    tags = []
    if "keywords" in docx_metadata:
        tags = [tag.strip() for tag in docx_metadata["keywords"].split(",")]
    
    # Determine title
    title = docx_metadata.get("title", "")
    if not title:
        # Use filename without extension as fallback title
        title = os.path.splitext(os.path.basename(file_path))[0]
    
    # Create result object
    result = {
        **metadata,
        **docx_metadata,
        "content": content,
        "title": title,
        "tags": tags
    }
    
    return result

def main():
    parser = argparse.ArgumentParser(
        description="Extract content and metadata from Word .docx files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    parser.add_argument('file', help="Input .docx file")
    parser.add_argument('-v', '--version', action='version', version='docx-extractor 1.0.0')
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