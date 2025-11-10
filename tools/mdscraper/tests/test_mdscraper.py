#!/usr/bin/env python3
"""
Tests for mdscraper tool
"""

import os
import sys
import tempfile
import unittest

# Add parent directory to path so we can import mdscraper module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mdscraper import (
    parse_ignore_file,
    should_ignore,
    scan_directory,
    extract_file_content,
)


class TestMdScraper(unittest.TestCase):
    """Tests for the mdscaper tool"""

    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.test_dir.name

        # Create some test files
        self.create_test_files()

    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()

    def create_test_files(self):
        # Create a sample .mdscraper file
        ignore_content = """
# Ignore patterns for mdscraper
*.log
temp/
!important.log
"""
        with open(os.path.join(self.dir_path, ".mdscraper"), "w") as f:
            f.write(ignore_content)

        # Create test text files
        with open(os.path.join(self.dir_path, "file1.txt"), "w") as f:
            f.write("This is file 1\nIt has some content.")

        with open(os.path.join(self.dir_path, "file2.txt"), "w") as f:
            f.write("This is file 2\nWith different content.")

        with open(os.path.join(self.dir_path, "test.log"), "w") as f:
            f.write("This is a log file that should be ignored.")

        with open(os.path.join(self.dir_path, "important.log"), "w") as f:
            f.write("This is an important log that should NOT be ignored.")

        # Create a subdirectory
        os.makedirs(os.path.join(self.dir_path, "subdir"), exist_ok=True)
        with open(os.path.join(self.dir_path, "subdir", "subfile.txt"), "w") as f:
            f.write("This is a file in a subdirectory.")

        # Create a temp directory that should be ignored
        os.makedirs(os.path.join(self.dir_path, "temp"), exist_ok=True)
        with open(os.path.join(self.dir_path, "temp", "tempfile.txt"), "w") as f:
            f.write("This file should be ignored.")

    def test_parse_ignore_file(self):
        """Test parsing the ignore file"""
        ignore_file = os.path.join(self.dir_path, ".mdscraper")
        patterns = parse_ignore_file(ignore_file)

        self.assertEqual(len(patterns), 3)
        self.assertIn("*.log", patterns)
        self.assertIn("temp/", patterns)
        self.assertIn("!important.log", patterns)

    def test_should_ignore(self):
        """Test the ignore pattern matching"""
        patterns = ["*.log", "temp/", "!important.log"]

        # Should be ignored
        self.assertTrue(should_ignore("test.log", patterns))
        self.assertTrue(should_ignore("temp/file.txt", patterns))
        self.assertTrue(
            should_ignore(".hidden", patterns)
        )  # Hidden files always ignored

        # Should NOT be ignored
        self.assertFalse(should_ignore("important.log", patterns))
        self.assertFalse(should_ignore("file.txt", patterns))

    def test_scan_directory(self):
        """Test scanning for files in a directory"""
        patterns = parse_ignore_file(os.path.join(self.dir_path, ".mdscraper"))

        # Non-recursive scan
        files = scan_directory(self.dir_path, patterns, recursive=False)

        # Verify it found the right files
        file_basenames = [os.path.basename(f) for f in files]
        self.assertIn("file1.txt", file_basenames)
        self.assertIn("file2.txt", file_basenames)
        self.assertIn("important.log", file_basenames)
        self.assertNotIn("test.log", file_basenames)
        self.assertNotIn("subfile.txt", file_basenames)  # Not found, not recursive

        # Recursive scan
        files = scan_directory(self.dir_path, patterns, recursive=True)

        # Verify it found recursive files too
        file_basenames = [os.path.basename(f) for f in files]
        self.assertIn("file1.txt", file_basenames)
        self.assertIn("file2.txt", file_basenames)
        self.assertIn("important.log", file_basenames)
        self.assertIn("subfile.txt", file_basenames)  # Found with recursive
        self.assertNotIn("test.log", file_basenames)
        self.assertNotIn("tempfile.txt", file_basenames)  # In ignored directory

    def test_extract_file_content(self):
        """Test extracting content from files"""
        file_path = os.path.join(self.dir_path, "file1.txt")
        content = extract_file_content(file_path)

        self.assertEqual(content, "This is file 1\nIt has some content.")


if __name__ == "__main__":
    unittest.main()
