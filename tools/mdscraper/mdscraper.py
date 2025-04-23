#!/usr/bin/env python3
"""
mdscraper: Combine text files into a single markdown document

Scans a directory for text files and combines them into a single markdown document.
Supports filtering through a .gitignore-style configuration file.

Usage: mdscraper [options] [directory]
       mdscraper -o output.md [directory]
       mdscraper --ignore-file .mdscraper [directory]

Options:
  -o, --output FILE          Write markdown to FILE instead of stdout
  -i, --ignore-file FILE     Use specified ignore file instead of .mdscraper
  -r, --recursive            Recursively process subdirectories
  --include-path             Include file paths as headers in the output
  --no-headers               Don't add file names as headers
  --toc                      Add table of contents at the beginning
"""
import sys
import os
import argparse
import fnmatch
import re


def parse_ignore_file(ignore_file_path):
    """Parse a .gitignore style file into a list of patterns."""
    if not os.path.exists(ignore_file_path):
        return []
    
    patterns = []
    with open(ignore_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            patterns.append(line)
    return patterns


def should_ignore(path, patterns):
    """Determine if a file should be ignored based on patterns."""
    # Always ignore hidden files
    if os.path.basename(path).startswith('.'):
        return True
    
    # Check for directory patterns - if path contains a directory that should be ignored
    if '/' in path:
        path_parts = path.split('/')
        for i in range(len(path_parts)):
            partial_path = '/'.join(path_parts[:i+1]) + '/'
            for pattern in patterns:
                if not pattern.startswith('!') and pattern.endswith('/') and fnmatch.fnmatch(partial_path, pattern):
                    # Check if there's a negation pattern that overrides
                    negation_overrides = False
                    for neg_pattern in patterns:
                        if neg_pattern.startswith('!') and fnmatch.fnmatch(path, neg_pattern[1:]):
                            negation_overrides = True
                            break
                    if not negation_overrides:
                        return True
    
    # Check if path matches any negation pattern first
    for pattern in patterns:
        if pattern.startswith('!'):
            if fnmatch.fnmatch(path, pattern[1:]):
                # If it matches a negation pattern, do not ignore
                return False
    
    # Then check if it matches any regular pattern
    for pattern in patterns:
        if not pattern.startswith('!') and not pattern.endswith('/'):
            if fnmatch.fnmatch(path, pattern):
                return True
    
    # Default: don't ignore
    return False


def scan_directory(directory, patterns, recursive=False):
    """Scan a directory for text files, filtering by ignore patterns."""
    files = []
    
    for item in os.listdir(directory):
        path = os.path.join(directory, item)
        rel_path = os.path.relpath(path, directory)
        
        if should_ignore(rel_path, patterns):
            continue
            
        if os.path.isfile(path):
            # Only include text files
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    f.read(1024)  # Try to read a bit to check if it's text
                files.append(path)
            except UnicodeDecodeError:
                # Skip binary files
                continue
        elif os.path.isdir(path) and recursive:
            # For directories, check if the directory itself should be ignored
            dir_path = rel_path + '/'
            if any(pattern.endswith('/') and fnmatch.fnmatch(dir_path, pattern) 
                  for pattern in patterns if not pattern.startswith('!')):
                # Directory matches an ignore pattern, skip it
                continue
                
            # Process subdirectories recursively if requested
            subdir_files = scan_directory(path, patterns, recursive)
            files.extend(subdir_files)
    
    # Sort files for consistent output
    return sorted(files)


def extract_file_content(file_path):
    """Extract content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        return f"ERROR: Could not decode {file_path} as UTF-8"


def create_toc(files, base_dir):
    """Create a table of contents from the list of files."""
    toc = ["# Table of Contents\n"]
    
    for file_path in files:
        rel_path = os.path.relpath(file_path, base_dir)
        file_name = os.path.basename(file_path)
        # Create a GitHub-style anchor link
        anchor = file_name.lower().replace(' ', '-')
        anchor = re.sub(r'[^\w-]', '', anchor)
        toc.append(f"- [{rel_path}](#{anchor})")
    
    return "\n".join(toc) + "\n\n"


def main():
    parser = argparse.ArgumentParser(
        description="Combine text files into a single markdown document"
    )
    parser.add_argument(
        "directory", 
        nargs="?", 
        default=".", 
        help="Directory to process (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output markdown file (default: stdout)"
    )
    parser.add_argument(
        "-i", "--ignore-file", 
        default=".mdscraper", 
        help="Gitignore-style file with patterns to ignore (default: .mdscraper)"
    )
    parser.add_argument(
        "-r", "--recursive", 
        action="store_true", 
        help="Recursively process subdirectories"
    )
    parser.add_argument(
        "--include-path", 
        action="store_true", 
        help="Include file paths as headers"
    )
    parser.add_argument(
        "--no-headers", 
        action="store_true", 
        help="Don't add file names as headers"
    )
    parser.add_argument(
        "--toc", 
        action="store_true", 
        help="Add table of contents"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="mdscraper 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Resolve the directory path
    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        return 1
    
    # Load ignore patterns
    ignore_file = args.ignore_file
    if not os.path.isabs(ignore_file):
        # First check if ignore file exists in specified directory
        dir_ignore_file = os.path.join(directory, ignore_file)
        if os.path.exists(dir_ignore_file):
            ignore_file = dir_ignore_file
    
    ignore_patterns = parse_ignore_file(ignore_file)
    
    # Always ignore the output file if specified
    if args.output:
        output_basename = os.path.basename(args.output)
        ignore_patterns.append(output_basename)
    
    # Scan for files
    files = scan_directory(directory, ignore_patterns, args.recursive)
    
    if not files:
        print(f"Warning: No text files found in {directory}", file=sys.stderr)
        return 0
    
    # Build the markdown content
    content = []
    
    # Add table of contents if requested
    if args.toc:
        content.append(create_toc(files, directory))
    
    # Process each file
    for file_path in files:
        rel_path = os.path.relpath(file_path, directory)
        file_name = os.path.basename(file_path)
        
        # Add header unless disabled
        if not args.no_headers:
            if args.include_path:
                content.append(f"# {rel_path}\n")
            else:
                content.append(f"# {file_name}\n")
        
        # Add file content
        file_content = extract_file_content(file_path)
        content.append(file_content)
        
        # Add separator between files
        content.append("\n---\n")
    
    # Remove the last separator if it exists
    if content and content[-1] == "\n---\n":
        content.pop()
    
    # Join all content
    markdown = "\n".join(content)
    
    # Output the result
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"Created '{args.output}'", file=sys.stderr)
    else:
        print(markdown)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())