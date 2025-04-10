#!/usr/bin/env python3
"""
pdf-extractor: Extract content and metadata from PDF files

Reads a PDF file and outputs a JSON object containing the file's content
and metadata including filename, size, page count, title, author, etc.

Usage: pdf-extractor [options] [FILE]

Examples:
  pdf-extractor document.pdf           # Extract from a PDF file
  cat document.pdf | pdf-extractor     # Read from stdin (if applicable)
"""
import sys
import os
import json
import argparse
import fitz  # PyMuPDF
from datetime import datetime
import mimetypes
from pathlib import Path
import tempfile

def get_file_metadata(file_path):
    """Get file metadata including creation time, modification time, size, etc."""
    path = Path(file_path)
    stat = path.stat()
    
    # Get file modification and creation times
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
    try:
        ctime = datetime.fromtimestamp(stat.st_ctime).isoformat()
    except:
        ctime = mtime  # Fallback if creation time not available
    
    # Get mime type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/pdf"  # Default to PDF
    
    return {
        "filename": path.name,
        "path": str(path.absolute()),
        "size": stat.st_size,
        "created_at": ctime,
        "modified_at": mtime,
        "mime_type": mime_type,
        "extension": path.suffix.lstrip(".") if path.suffix else "pdf"
    }

def extract_pdf_content(file_path):
    """Extract content and metadata from a PDF file."""
    try:
        doc = fitz.open(file_path)
        
        # Extract PDF metadata
        pdf_metadata = {
            "page_count": doc.page_count,
            "title": doc.metadata.get('title', ''),
            "author": doc.metadata.get('author', ''),
            "subject": doc.metadata.get('subject', ''),
            "keywords": doc.metadata.get('keywords', ''),
            "creator": doc.metadata.get('creator', ''),
            "producer": doc.metadata.get('producer', ''),
            "creation_date": doc.metadata.get('creationDate', ''),
            "modification_date": doc.metadata.get('modDate', '')
        }
        
        # Extract text content from all pages
        content = ""
        for page_num in range(doc.page_count):
            page = doc[page_num]
            content += page.get_text()
            content += "\n\n"  # Add spacing between pages
        
        doc.close()
        return content, pdf_metadata
    except Exception as e:
        sys.stderr.write(f"Error extracting PDF content: {e}\n")
        return "", {}

def process_file(file_path):
    """Extract content and metadata from the file."""
    # Check if we're dealing with stdin or a file
    temp_file = None
    
    try:
        if not file_path or file_path == '-':
            # Reading from stdin, save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(sys.stdin.buffer.read())
            temp_file.close()
            file_path = temp_file.name
            
            # Create basic metadata for stdin input
            metadata = {
                "filename": "stdin",
                "path": "stdin",
                "size": os.path.getsize(file_path),
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "mime_type": "application/pdf",
                "extension": "pdf"
            }
        else:
            # Reading from a file
            if not os.path.exists(file_path):
                sys.stderr.write(f"Error: File '{file_path}' not found.\n")
                return {}
                
            # Get file metadata
            metadata = get_file_metadata(file_path)
        
        # Extract PDF content and PDF-specific metadata
        content, pdf_metadata = extract_pdf_content(file_path)
        
        # Create result object
        result = {
            **metadata,
            **pdf_metadata,
            "content": content,
            "title": pdf_metadata.get("title") or metadata["filename"],
            "tags": [tag.strip() for tag in pdf_metadata.get("keywords", "").split(",")] if pdf_metadata.get("keywords") else []
        }
        
        return result
    finally:
        # Clean up the temporary file if one was created
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def main():
    parser = argparse.ArgumentParser(
        description="Extract content and metadata from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    parser.add_argument('file', nargs='?', help="Input file (default: stdin)")
    parser.add_argument('-v', '--version', action='version', version='pdf-extractor 1.0.0')
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