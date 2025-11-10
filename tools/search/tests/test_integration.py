#!/usr/bin/env python3
"""
Integration tests for the search tool.

This script demonstrates how the search tool would be used in practice.
It sets up collections, indexes files, and performs searches.

NOTE: These tests are not fully automated and require manual verification.
They are meant to be used as a demonstration of the tool's functionality.
"""

import os
import sys
import shutil

# Add parent directory to path so we can import the search module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import search

# Get the path to the test data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DOCS_DIR = os.path.join(DATA_DIR, "docs")
PAPERS_DIR = os.path.join(DATA_DIR, "papers")


def setup_collections():
    """Set up test collections."""
    print("\n=== Setting up test collections ===")

    # Initialize docs collection
    print("\nInitializing docs collection...")

    class DocsArgs:
        directory = DOCS_DIR
        name = "Test Documents"
        include = ["*.md", "*.txt"]
        exclude = None
        extract = None
        force = True

    result = search.cmd_init(DocsArgs())  # type: ignore
    print(f"Result: {result}")

    # Initialize papers collection
    print("\nInitializing papers collection...")

    class PapersArgs:
        directory = PAPERS_DIR
        name = "Research Papers"
        include = ["*.md"]
        exclude = None
        extract = None
        force = True

    result = search.cmd_init(PapersArgs())  # type: ignore
    print(f"Result: {result}")


def scan_collections():
    """Scan for collections."""
    print("\n=== Scanning for collections ===")

    class ScanArgs:
        directory = DATA_DIR

    search.cmd_scan(ScanArgs())  # type: ignore


def index_collections():
    """Index the test collections."""
    print("\n=== Indexing collections ===")

    class IndexArgs:
        directories = [DOCS_DIR, PAPERS_DIR]
        verbose = True
        no_cache = False

    search.cmd_index(IndexArgs())  # type: ignore


def search_collections():
    """Perform searches on the indexed collections."""
    print("\n=== Searching collections ===")

    # Search for 'machine learning'
    print("\nSearching for 'machine learning'...")

    class QueryArgs1:
        query = "machine learning"
        in_dir = None
        tag = None
        limit = 5
        verbose = True

    search.cmd_query(QueryArgs1())  # type: ignore

    # Search for 'neural networks'
    print("\nSearching for 'neural networks'...")

    class QueryArgs2:
        query = "neural networks"
        in_dir = None
        tag = None
        limit = 5
        verbose = True

    search.cmd_query(QueryArgs2())  # type: ignore

    # Search with tag filter
    print("\nSearching for documents tagged with 'ai'...")

    class QueryArgs3:
        query = ""
        in_dir = None
        tag = "ai"
        limit = 5
        verbose = True

    search.cmd_query(QueryArgs3())  # type: ignore

    # Search in specific collection
    print("\nSearching in papers collection only...")

    class QueryArgs4:
        query = "learning"
        in_dir = PAPERS_DIR
        tag = None
        limit = 5
        verbose = True

    search.cmd_query(QueryArgs4())  # type: ignore


def cleanup():
    """Clean up the test collections."""
    print("\n=== Cleaning up test collections ===")

    # Remove the .search directories
    shutil.rmtree(os.path.join(DOCS_DIR, ".search"), ignore_errors=True)
    shutil.rmtree(os.path.join(PAPERS_DIR, ".search"), ignore_errors=True)

    print("Cleanup complete.")


def main():
    """Run the integration tests."""
    try:
        print("Starting integration tests...")

        # Set up collections
        setup_collections()

        # Scan for collections
        scan_collections()

        # Index collections
        index_collections()

        # Search collections
        search_collections()

        # Clean up
        cleanup()

        print("\nIntegration tests completed successfully!")
        return 0
    except Exception as e:
        print(f"Error during integration tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
