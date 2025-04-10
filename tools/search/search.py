#!/usr/bin/env python3
"""
search: Manage self-contained searchable collections of files

A modular, low-resource, local search system for files (PDFs, images, videos, etc.)
where each collection is self-contained and can be indexed and queried using Tantivy.

Usage:
  search init [options] [directory]      Initialize a directory as a search collection
  search scan [options] [directory]      Find all search collections in a directory tree
  search index [options] [directory...]  Index all matched files in one or more collections
  search query [options] QUERY           Search indexed collections using Tantivy

Examples:
  search init ~/documents                     # Initialize a collection
  search init --name "Research" ~/papers      # Initialize with a specific name
  search init --extract "*.pdf=pdf2md {input}"  # Add a specific extractor

  search scan ~/documents                     # Find collections

  search index ~/documents                    # Index a single collection
  search index ~/documents ~/papers           # Index multiple collections
  search index --verbose ~/documents          # Show detailed indexing progress

  search query "neural networks"              # Search across all nearby collections
  search query "DNA" --in ~/papers            # Search in a specific collection
  search query "protein" --tag biology        # Search with tag filter
  search query "machine learning" --limit 10  # Limit number of results

For more detailed help on a specific subcommand:
  search init --help
  search scan --help
  search index --help
  search query --help
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import toml

# Try to import Tantivy, but don't fail immediately if not available
# This allows --help and other non-search operations to work without Tantivy
try:
    import tantivy

    TANTIVY_AVAILABLE = True
except ImportError:
    TANTIVY_AVAILABLE = False


def check_tantivy():
    """Check if Tantivy is available and exit if not."""
    if not TANTIVY_AVAILABLE:
        print(
            "Error: Required Tantivy Python bindings not found. Please install them with:"
        )
        print("    pip install tantivy")
        sys.exit(1)


# Constants
SEARCH_DIR = ".search"
CONFIG_FILE = f"{SEARCH_DIR}/config.toml"
CACHE_DIR = f"{SEARCH_DIR}/cache"
INDEX_DIR = f"{SEARCH_DIR}/index"

# Default extractor commands for common file types
DEFAULT_EXTRACTORS = {
    "*.md": "text-extractor {input}",
    "*.txt": "text-extractor {input}",
    "*.pdf": "pdf-extractor {input}",
    "*.docx": "docx-extractor {input}",
}

# Default configuration
DEFAULT_CONFIG = {
    "name": "Default Collection",
    "include": {"patterns": ["*.pdf", "*.md", "*.txt", "*.docx"]},
    "exclude": {"patterns": ["*~", "*.bak", "*.tmp", ".git/*", ".search/*"]},
    "extractors": DEFAULT_EXTRACTORS,
    "output": {"format": "json", "directory": "cache"},
}


def ensure_dir(path: str) -> None:
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def find_collections(start_dir: str) -> List[str]:
    """Find all search collections starting from a directory."""
    collections = []
    start_path = Path(start_dir).resolve()

    for path in start_path.glob(f"**/{SEARCH_DIR}"):
        config_file = path / "config.toml"
        if config_file.exists():
            collections.append(str(path.parent))

    return collections


def load_config(collection_dir: str) -> Dict[str, Any]:
    """Load collection configuration."""
    config_path = os.path.join(collection_dir, CONFIG_FILE)
    try:
        with open(config_path, "r") as f:
            return toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        sys.stderr.write(f"Error loading config: {e}\n")
        return {}


def save_config(collection_dir: str, config: Dict[str, Any]) -> bool:
    """Save collection configuration."""
    config_path = os.path.join(collection_dir, CONFIG_FILE)
    try:
        # Ensure the .search directory exists
        ensure_dir(os.path.join(collection_dir, SEARCH_DIR))

        with open(config_path, "w") as f:
            toml.dump(config, f)
        return True
    except Exception as e:
        sys.stderr.write(f"Error saving config: {e}\n")
        return False


def filter_files(collection_dir: str, config: Dict[str, Any]) -> List[str]:
    """Filter files based on include/exclude patterns."""
    include_patterns = config.get("include", {}).get("patterns", ["*"])
    exclude_patterns = config.get("exclude", {}).get("patterns", [])

    matched_files = []

    # Walk the directory tree
    for root, dirs, files in os.walk(collection_dir):
        # Skip the .search directory
        if os.path.basename(root) == SEARCH_DIR:
            continue

        # Check if any exclude pattern matches directories
        skip_dir = False
        for pattern in exclude_patterns:
            if any(fnmatch.fnmatch(d, pattern) for d in dirs):
                skip_dir = True
                break
        if skip_dir:
            continue

        # Match files against include/exclude patterns
        for filename in files:
            file_path = os.path.join(root, filename)

            # Skip if the file is in the .search directory
            if SEARCH_DIR in file_path.split(os.sep):
                continue

            # Check include patterns
            if not any(
                fnmatch.fnmatch(filename, pattern) for pattern in include_patterns
            ):
                continue

            # Check exclude patterns
            if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                continue

            matched_files.append(file_path)

    return matched_files


def get_extractor(filename: str, config: Dict[str, Any]) -> Optional[str]:
    """Find the appropriate extractor command for a file."""
    extractors = config.get("extractors", {})

    for pattern, command in extractors.items():
        if fnmatch.fnmatch(filename, pattern):
            return command

    return None


def extract_metadata(file_path: str, extractor_cmd: str) -> Dict[str, Any]:
    """Execute extractor and parse output as JSON."""
    # Replace {input} with the file path
    cmd = extractor_cmd.replace("{input}", file_path)

    try:
        # Run the extractor command
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        output = result.stdout

        # Attempt to parse as JSON
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # If parsing fails, create basic metadata with content
            return {"title": os.path.basename(file_path), "content": output}
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error executing extractor for {file_path}: {e}\n")
        return {}


def save_cache(
    collection_dir: str,
    file_path: str,
    metadata: Dict[str, Any],
    config: Dict[str, Any],
) -> bool:
    """Save metadata to cache."""
    # Ensure the cache directory exists
    cache_dir = os.path.join(collection_dir, CACHE_DIR)
    ensure_dir(cache_dir)

    # Create a cache file name based on the original file path
    rel_path = os.path.relpath(file_path, collection_dir)
    cache_filename = re.sub(r"[/\\]", "_", rel_path)

    # Save as JSON
    cache_path = os.path.join(cache_dir, f"{cache_filename}.json")
    try:
        with open(cache_path, "w") as f:
            json.dump(metadata, f, indent=2)
        return True
    except Exception as e:
        sys.stderr.write(f"Error saving cache file {cache_path}: {e}\n")
        return False


def create_schema():
    """Create Tantivy schema for document indexing."""
    schema_builder = tantivy.SchemaBuilder()

    # Define fields for the schema
    schema_builder.add_text_field("path", stored=True)
    schema_builder.add_text_field("title", stored=True)
    schema_builder.add_text_field("content", stored=True)
    schema_builder.add_text_field("absolute_path", stored=True)
    # Using text fields for tags instead of facets
    schema_builder.add_text_field("tag_pdf", stored=True)
    schema_builder.add_text_field("tag_test", stored=True)
    schema_builder.add_text_field("tag_sample", stored=True)
    # Add more common tags as needed
    schema_builder.add_text_field(
        "metadata", stored=True
    )  # For storing additional JSON metadata

    return schema_builder.build()


def get_or_create_index(collection_dir: str) -> tuple:
    """Get or create a Tantivy index for a collection."""
    # Check if Tantivy is available
    check_tantivy()

    index_dir = os.path.join(collection_dir, INDEX_DIR)
    ensure_dir(index_dir)

    # For reference only - we don't actually read this
    schema_path = os.path.join(index_dir, "schema_info.json")

    # Check if index exists
    if os.path.exists(os.path.join(index_dir, "meta.json")):
        # Try to open existing index
        try:
            index = tantivy.Index.open(index_dir)
            return index, None  # We don't need the schema for opened indexes
        except Exception as e:
            # If opening failed, create a new one
            sys.stderr.write(
                f"Warning: Could not open existing index, creating new one: {e}\n"
            )

    # Create new schema and index
    schema = create_schema()
    # Create basic schema info for reference
    schema_info = {
        "fields": [
            {"name": "path", "type": "text", "stored": True},
            {"name": "title", "type": "text", "stored": True},
            {"name": "content", "type": "text", "stored": True},
            {"name": "absolute_path", "type": "text", "stored": True},
            {"name": "tag_pdf", "type": "text", "stored": True},
            {"name": "tag_test", "type": "text", "stored": True},
            {"name": "tag_sample", "type": "text", "stored": True},
            {"name": "metadata", "type": "text", "stored": True},
        ]
    }

    # Save schema info for reference
    with open(schema_path, "w") as f:
        json.dump(schema_info, f, indent=2)

    # Create the index
    index = tantivy.Index(schema, path=index_dir)
    return index, schema


def index_file(collection_dir: str, file_path: str, metadata: Dict[str, Any]) -> bool:
    """Index a file using Tantivy."""
    try:
        # Get or create index
        index, schema = get_or_create_index(collection_dir)

        # Create a writer for adding documents
        writer = index.writer()

        # Create document
        doc = tantivy.Document()

        # Get relative path as identifier
        rel_path = os.path.relpath(file_path, collection_dir)

        # Add fields to document
        doc.add_text("path", rel_path)
        doc.add_text("absolute_path", os.path.abspath(file_path))

        # Add title if available
        if "title" in metadata and metadata["title"]:
            doc.add_text("title", metadata["title"])
        else:
            doc.add_text("title", os.path.basename(file_path))

        # Add content if available
        if "content" in metadata and metadata["content"]:
            doc.add_text("content", metadata["content"])

        # Add tags as facets if available
        if "tags" in metadata and isinstance(metadata["tags"], list):
            for tag in metadata["tags"]:
                if tag and isinstance(tag, str):
                    # Add as text since facets are complicated in Tantivy
                    tag_field = f"tag_{tag.lower().replace(' ', '_').replace(',', '').replace('-', '_')}"
                    doc.add_text(tag_field, "true")

        # Store all metadata as JSON
        doc.add_text(
            "metadata",
            json.dumps(
                {
                    "path": rel_path,
                    "absolute_path": os.path.abspath(file_path),
                    **metadata,
                }
            ),
        )

        # Add document to index
        writer.add_document(doc)

        # Commit changes
        writer.commit()
        return True
    except Exception as e:
        sys.stderr.write(f"Error indexing file {file_path}: {e}\n")
        return False


def perform_search(
    query_string: str,
    collections: List[str],
    tag_filter: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search across collections using Tantivy."""
    # Check if Tantivy is available
    check_tantivy()

    results = []

    # Process each collection
    for collection_dir in collections:
        index_dir = os.path.join(collection_dir, INDEX_DIR)
        if not os.path.exists(index_dir) or not os.path.exists(
            os.path.join(index_dir, "meta.json")
        ):
            continue

        try:
            # Open the index
            index = tantivy.Index.open(index_dir)
            searcher = index.searcher()

            # Parse the query using index's parse_query method
            query = index.parse_query(query_string, ["title", "content"])

            # Perform the search
            search_result = searcher.search(query, limit)

            # Extract results - access the hits property which contains doc_address
            for hit in search_result.hits:
                # Unpack score and doc_address from the hit
                score, doc_address = hit
                retrieved_doc = searcher.doc(doc_address)

                # Create basic metadata
                title = ""
                path = ""
                abs_path = ""
                tags = []
                score_value = score * 100  # Convert to percentage

                # Extract fields using get_first
                title_field = retrieved_doc.get_first("title")
                if title_field:
                    title = title_field

                path_field = retrieved_doc.get_first("path")
                if path_field:
                    path = path_field

                abs_path_field = retrieved_doc.get_first("absolute_path")
                if abs_path_field:
                    abs_path = abs_path_field

                metadata_field = retrieved_doc.get_first("metadata")
                if metadata_field:
                    try:
                        metadata = json.loads(metadata_field)
                        # If we have tags in metadata, extract them
                        if "tags" in metadata:
                            tags = metadata["tags"]
                    except:
                        pass

                # Skip documents that don't match tag filter
                if tag_filter and tag_filter.lower() not in [t.lower() for t in tags]:
                    continue

                # Create result object
                data = {
                    "title": title or os.path.basename(path),
                    "path": path,
                    "absolute_path": abs_path,
                    "tags": tags,
                    "score": score_value,
                    "collection": os.path.basename(collection_dir),
                    "collection_path": collection_dir,
                }

                results.append(data)
        except Exception as e:
            sys.stderr.write(f"Error searching in collection {collection_dir}: {e}\n")

    # Sort results by score (highest first)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return results[:limit]


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a directory as a search collection."""
    directory = os.path.abspath(args.directory or os.getcwd())

    # Check if the directory exists
    if not os.path.isdir(directory):
        sys.stderr.write(f"Error: Directory {directory} does not exist.\n")
        return 1

    # Check if the collection already exists
    config_path = os.path.join(directory, CONFIG_FILE)
    if os.path.exists(config_path):
        if not args.force:
            sys.stderr.write(
                f"Error: Collection already exists at {directory}. Use --force to overwrite.\n"
            )
            return 1

    # Create the basic configuration
    config = DEFAULT_CONFIG.copy()

    # Update configuration based on command-line arguments
    if args.name:
        config["name"] = args.name

    if args.include:
        config["include"]["patterns"] = args.include

    if args.exclude:
        config["exclude"]["patterns"] = args.exclude

    # Add custom extractors if specified
    if args.extract:
        extractors = config["extractors"].copy()
        for extractor in args.extract:
            if "=" in extractor:
                pattern, command = extractor.split("=", 1)
                extractors[pattern.strip()] = command.strip()
        config["extractors"] = extractors

    # Create the directory structure
    ensure_dir(os.path.join(directory, SEARCH_DIR))
    ensure_dir(os.path.join(directory, CACHE_DIR))
    ensure_dir(os.path.join(directory, INDEX_DIR))

    # Save the configuration
    if save_config(directory, config):
        print(f"Initialized search collection in {directory}")
        print(f"Configuration saved to {config_path}")
        return 0
    else:
        return 1


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan for collections."""
    directory = os.path.abspath(args.directory or os.getcwd())

    if not os.path.isdir(directory):
        sys.stderr.write(f"Error: Directory {directory} does not exist.\n")
        return 1

    collections = find_collections(directory)

    if not collections:
        print(f"No search collections found in {directory}")
        return 0

    print(f"Found {len(collections)} search collection(s):")
    for collection in collections:
        config = load_config(collection)
        name = config.get("name", "Unnamed collection")
        print(f"  {name}: {collection}")

    return 0


def cmd_index(args: argparse.Namespace) -> int:
    """Index files in collections."""
    directories = (
        [os.path.abspath(d) for d in args.directories]
        if args.directories
        else [os.getcwd()]
    )

    collections = []
    for directory in directories:
        # Check if the directory is a collection
        if os.path.exists(os.path.join(directory, CONFIG_FILE)):
            collections.append(directory)
        else:
            # Scan for collections in this directory
            found_collections = find_collections(directory)
            collections.extend(found_collections)

    if not collections:
        sys.stderr.write(
            f"Error: No search collections found in the specified directories.\n"
        )
        return 1

    indexed_count = 0
    failed_count = 0

    for collection_dir in collections:
        config = load_config(collection_dir)
        if not config:
            sys.stderr.write(
                f"Warning: Skipping collection {collection_dir} due to missing or invalid configuration.\n"
            )
            continue

        collection_name = config.get("name", os.path.basename(collection_dir))
        print(f"Indexing collection: {collection_name} ({collection_dir})")

        # Get matched files
        matched_files = filter_files(collection_dir, config)
        print(f"Found {len(matched_files)} matching files")

        for file_path in matched_files:
            rel_path = os.path.relpath(file_path, collection_dir)

            try:
                # Get the appropriate extractor
                extractor = get_extractor(os.path.basename(file_path), config)
                if not extractor:
                    if args.verbose:
                        print(f"  Skipping {rel_path}: No extractor found")
                    continue

                if args.verbose:
                    print(f"  Extracting {rel_path}")

                # Extract metadata
                metadata = extract_metadata(file_path, extractor)
                if not metadata:
                    if args.verbose:
                        print(f"  Failed to extract metadata from {rel_path}")
                    failed_count += 1
                    continue

                # Save to cache if caching is enabled
                if not args.no_cache:
                    save_cache(collection_dir, file_path, metadata, config)

                # Index the file
                if index_file(collection_dir, file_path, metadata):
                    indexed_count += 1
                    if args.verbose:
                        print(f"  Successfully indexed {rel_path}")
                else:
                    failed_count += 1
                    if args.verbose:
                        print(f"  Failed to index {rel_path}")
            except Exception as e:
                sys.stderr.write(f"Error processing {rel_path}: {e}\n")
                failed_count += 1

    print(
        f"Finished indexing {indexed_count} files across {len(collections)} collections."
    )
    if failed_count > 0:
        print(f"Failed to index {failed_count} files.")

    return 0 if failed_count == 0 else 1


def cmd_query(args: argparse.Namespace) -> int:
    """Search collections."""
    # Check if Tantivy is available
    check_tantivy()

    # Determine which collections to search
    collections = []
    if args.in_dir:
        directory = os.path.abspath(args.in_dir)
        if os.path.exists(os.path.join(directory, CONFIG_FILE)):
            collections.append(directory)
        else:
            sys.stderr.write(f"Error: {directory} is not a valid search collection.\n")
            return 1
    else:
        # Start from current directory, search up to find collections
        dir_path = os.path.abspath(os.getcwd())
        while dir_path and dir_path != "/":
            if os.path.exists(os.path.join(dir_path, CONFIG_FILE)):
                collections.append(dir_path)
                break
            dir_path = os.path.dirname(dir_path)

        # If no collection is found, scan for collections in current directory
        if not collections:
            collections = find_collections(os.getcwd())

    if not collections:
        sys.stderr.write(
            "Error: No search collections found. Use --in to specify a collection.\n"
        )
        return 1

    # Perform the search
    results = perform_search(
        query_string=args.query,
        collections=collections,
        tag_filter=args.tag,
        limit=args.limit,
    )

    if not results:
        print(f"No results found for '{args.query}'")
        return 0

    print(f"Found {len(results)} results for '{args.query}':")

    for i, result in enumerate(results, 1):
        title = result.get("title", os.path.basename(result.get("path", "Unknown")))
        path = result.get("absolute_path", "Unknown path")
        score = result.get("score", 0)
        collection = result.get("collection", "Unknown collection")

        print(f"\n{i}. {title} ({score:.0f}% match) - {collection}")
        print(f"   Path: {path}")

        # Show tags if available
        tags = result.get("tags", [])
        if tags:
            print(f"   Tags: {', '.join(tags)}")

        # Show a snippet of content if available and detailed output is requested
        if args.verbose and "content" in result:
            content = result["content"]
            if content:
                # Truncate and sanitize for display
                content = re.sub(r"\s+", " ", content)
                snippet = content[:200] + ("..." if len(content) > 200 else "")
                print(f"   Snippet: {snippet}")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage searchable collections of files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1],  # Use the docstring as extended help
    )
    parser.add_argument("--version", action="version", version="search 1.0.0")

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize a directory as a search collection"
    )
    init_parser.add_argument(
        "directory",
        nargs="?",
        help="Directory to initialize (default: current directory)",
    )
    init_parser.add_argument("--name", help="Name for the collection")
    init_parser.add_argument(
        "--include", nargs="+", help='Include patterns (e.g., "*.pdf" "*.md")'
    )
    init_parser.add_argument(
        "--exclude", nargs="+", help='Exclude patterns (e.g., "*.bak" "draft_*")'
    )
    init_parser.add_argument(
        "--extract", nargs="+", help='Extractor patterns (e.g., "*.pdf=pdf2md {input}")'
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite if collection already exists",
    )

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="Find all search collections in a directory tree"
    )
    scan_parser.add_argument(
        "directory", nargs="?", help="Directory to scan (default: current directory)"
    )

    # index command
    index_parser = subparsers.add_parser(
        "index", help="Index all matched files in one or more collections"
    )
    index_parser.add_argument(
        "directories",
        nargs="*",
        help="Directories to index (default: current directory)",
    )
    index_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed progress"
    )
    index_parser.add_argument(
        "--no-cache", action="store_true", help="Skip caching extracted metadata"
    )

    # query command
    query_parser = subparsers.add_parser(
        "query", help="Search indexed collections using Tantivy"
    )
    query_parser.add_argument("query", help="Search query")
    query_parser.add_argument(
        "--in", dest="in_dir", help="Search in specific collection"
    )
    query_parser.add_argument("--tag", help="Filter by tag")
    query_parser.add_argument(
        "--limit", type=int, default=20, help="Maximum number of results (default: 20)"
    )
    query_parser.add_argument(
        "--verbose", action="store_true", help="Show more detailed results"
    )

    # Parse arguments
    args = parser.parse_args()

    # Execute the appropriate command
    if args.command == "init":
        return cmd_init(args)
    elif args.command == "scan":
        return cmd_scan(args)
    elif args.command == "index":
        return cmd_index(args)
    elif args.command == "query":
        return cmd_query(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
