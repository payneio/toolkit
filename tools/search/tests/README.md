# Search Tool Tests

This directory contains tests for the search tool.

## Unit Tests

The `test_search.py` file contains unit tests for various components of the search tool, including:

- Initialization
- Collection scanning
- File filtering
- Extractor matching

To run the unit tests:

```bash
cd /data/repos/toolkit/tools/search/tests
python3 test_search.py
```

## Integration Tests

The `test_integration.py` file demonstrates how the search tool would be used in a real workflow. It:

1. Sets up test collections
2. Indexes test files
3. Performs various searches
4. Cleans up the test collections

To run the integration tests:

```bash
cd /data/repos/toolkit/tools/search/tests
python3 test_integration.py
```

## Test Data

The `data/` directory contains sample files for testing:

- `data/docs/` - Simple text and markdown files
- `data/papers/` - Markdown files simulating research papers

These files are used by the integration tests to demonstrate the search tool's functionality.

## Dependencies

The tests require the Tantivy Python bindings to be installed:

```bash
pip install tantivy-py
```

If you encounter "no binary wheel" errors, you'll need to install Rust first:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
pip install tantivy-py
```