#!/usr/bin/env python3
"""
Unit tests for the search tool.
"""

import os
import sys
import tempfile
import unittest
import shutil

print(sys.executable)
print(sys.path)

# Add parent directory to path so we can import the search module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import search


class TestSearchInit(unittest.TestCase):
    """Test the initialization functionality."""

    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory after testing."""
        shutil.rmtree(self.test_dir)

    def test_init_creates_directory_structure(self):
        """Test that init creates the required directory structure."""

        # Create a mock args object
        class Args:
            directory = None
            name = "Test Collection"
            include = None
            exclude = None
            extract = None
            force = False

        args = Args()
        args.directory = self.test_dir

        # Run the init command
        result = search.cmd_init(args)

        # Check the result
        self.assertEqual(result, 0)

        # Check that the search directory was created
        search_dir = os.path.join(self.test_dir, search.SEARCH_DIR)
        self.assertTrue(os.path.isdir(search_dir))

        # Check that the cache directory was created
        cache_dir = os.path.join(self.test_dir, search.CACHE_DIR)
        self.assertTrue(os.path.isdir(cache_dir))

        # Check that the index directory was created
        index_dir = os.path.join(self.test_dir, search.INDEX_DIR)
        self.assertTrue(os.path.isdir(index_dir))

        # Check that the config file was created
        config_path = os.path.join(self.test_dir, search.CONFIG_FILE)
        self.assertTrue(os.path.isfile(config_path))

        # Load the config and check its values
        config = search.load_config(self.test_dir)
        self.assertEqual(config["name"], "Test Collection")
        self.assertIn("include", config)
        self.assertIn("patterns", config["include"])
        self.assertIn("exclude", config)
        self.assertIn("patterns", config["exclude"])
        self.assertIn("extractors", config)


class TestSearchScan(unittest.TestCase):
    """Test the scan functionality."""

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.test_dir = tempfile.mkdtemp()

        # Create a collection in the root directory
        os.makedirs(os.path.join(self.test_dir, search.SEARCH_DIR))
        with open(os.path.join(self.test_dir, search.CONFIG_FILE), "w") as f:
            f.write('name = "Root Collection"\n')

        # Create a nested collection
        nested_dir = os.path.join(self.test_dir, "nested")
        os.makedirs(os.path.join(nested_dir, search.SEARCH_DIR))
        with open(os.path.join(nested_dir, search.CONFIG_FILE), "w") as f:
            f.write('name = "Nested Collection"\n')

        # Create a directory without a collection
        os.makedirs(os.path.join(self.test_dir, "not_collection"))

    def tearDown(self):
        """Remove the temporary directory after testing."""
        shutil.rmtree(self.test_dir)

    def test_find_collections(self):
        """Test that find_collections finds all collections."""
        collections = search.find_collections(self.test_dir)

        # Normalize paths for comparison
        collections = [os.path.normpath(p) for p in collections]
        expected = [
            os.path.normpath(self.test_dir),
            os.path.normpath(os.path.join(self.test_dir, "nested")),
        ]

        # Check that both collections were found
        self.assertEqual(len(collections), 2)
        for path in expected:
            self.assertIn(path, collections)


class TestSearchFileMatching(unittest.TestCase):
    """Test file matching functionality."""

    def setUp(self):
        """Create a temporary directory with test files."""
        self.test_dir = tempfile.mkdtemp()

        # Create the search directory
        os.makedirs(os.path.join(self.test_dir, search.SEARCH_DIR))

        # Create test files
        with open(os.path.join(self.test_dir, "document.pdf"), "w") as f:
            f.write("PDF content")

        with open(os.path.join(self.test_dir, "notes.md"), "w") as f:
            f.write("# Markdown notes")

        with open(os.path.join(self.test_dir, "draft_document.pdf"), "w") as f:
            f.write("Draft content")

        # Create a nested directory with files
        nested_dir = os.path.join(self.test_dir, "nested")
        os.makedirs(nested_dir)

        with open(os.path.join(nested_dir, "nested.txt"), "w") as f:
            f.write("Nested text file")

        # Create a .search subdirectory with a file that should be excluded
        with open(
            os.path.join(self.test_dir, search.SEARCH_DIR, "config.bak"), "w"
        ) as f:
            f.write("Backup config")

    def tearDown(self):
        """Remove the temporary directory after testing."""
        shutil.rmtree(self.test_dir)

    def test_filter_files(self):
        """Test that filter_files correctly filters files."""
        config = {
            "include": {"patterns": ["*.pdf", "*.md", "*.txt"]},
            "exclude": {"patterns": ["draft_*", "*.bak"]},
        }

        matched_files = search.filter_files(self.test_dir, config)

        # Normalize paths for comparison
        matched_files = [os.path.normpath(p) for p in matched_files]

        # Check that the correct files were matched
        self.assertEqual(len(matched_files), 3)
        self.assertIn(
            os.path.normpath(os.path.join(self.test_dir, "document.pdf")), matched_files
        )
        self.assertIn(
            os.path.normpath(os.path.join(self.test_dir, "notes.md")), matched_files
        )
        self.assertIn(
            os.path.normpath(os.path.join(self.test_dir, "nested", "nested.txt")),
            matched_files,
        )

        # Check that excluded files were not matched
        self.assertNotIn(
            os.path.normpath(os.path.join(self.test_dir, "draft_document.pdf")),
            matched_files,
        )
        self.assertNotIn(
            os.path.normpath(
                os.path.join(self.test_dir, search.SEARCH_DIR, "config.bak")
            ),
            matched_files,
        )


class TestSearchExtractor(unittest.TestCase):
    """Test extractor functionality."""

    def test_get_extractor(self):
        """Test that get_extractor finds the correct extractor."""
        config = {
            "extractors": {
                "*.pdf": "pdf2md {input}",
                "*.md": "cat {input}",
                "*.docx": "docx2md {input}",
            }
        }

        # Check PDF extractor
        extractor = search.get_extractor("document.pdf", config)
        self.assertEqual(extractor, "pdf2md {input}")

        # Check Markdown extractor
        extractor = search.get_extractor("notes.md", config)
        self.assertEqual(extractor, "cat {input}")

        # Check DOCX extractor
        extractor = search.get_extractor("document.docx", config)
        self.assertEqual(extractor, "docx2md {input}")

        # Check for unsupported file type
        extractor = search.get_extractor("image.jpg", config)
        self.assertIsNone(extractor)


if __name__ == "__main__":
    unittest.main()
