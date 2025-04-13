#!/usr/bin/env python3
"""
Tests for docx2md.py CommonMark conversion.
"""
import sys
import unittest
import os
from io import StringIO
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import docx2md
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import docx2md


class TestMarkdownFormatting(unittest.TestCase):
    """Test that the markdown formatting function handles basic cases."""
    
    def test_heading_spacing(self):
        """Test that headings have empty lines after them."""
        input_md = """# Heading 1
Some text here."""
        
        result = docx2md.fix_markdown_formatting(input_md)
        
        # There should be an empty line between the heading and the text
        self.assertIn("# Heading 1\n\nSome text", result)


class TestDocxMdCommand(unittest.TestCase):
    """Test the CLI interface with mocked subprocess call."""
    
    @patch('subprocess.run')
    def test_cli_preserves_commonmark_format(self, mock_run):
        """Test that the CLI preserves CommonMark formatting."""
        # Create a mock return value with CommonMark-formatted content
        mock_process = MagicMock()
        mock_process.stdout = "# Title\n\n- Item 1\n\n- Item 2\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Capture stdout to validate the content is preserved
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['docx2md', 'fake.docx']):
                docx2md.main()
            
            output = fake_out.getvalue()
            # With CommonMark, we expect to preserve the format, not change it
            self.assertIn("# Title\n\n- Item 1\n\n- Item 2", output)
    
    @patch('subprocess.run')
    def test_cli_without_formatting_preserves_original(self, mock_run):
        """Test that --no-format preserves original formatting."""
        # Create a mock return value
        mock_process = MagicMock()
        mock_process.stdout = "# Title\n\n- Item 1\n\n- Item 2\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Capture stdout to validate no formatting is applied
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['docx2md', '--no-format', 'fake.docx']):
                docx2md.main()
            
            output = fake_out.getvalue()
            # Verify the original formatting is preserved
            self.assertIn("# Title\n\n- Item 1\n\n- Item 2", output)


if __name__ == '__main__':
    unittest.main()