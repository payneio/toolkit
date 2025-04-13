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
        
    def test_simple_list_formatting(self):
        """Test that simple lists have no empty lines between items."""
        input_md = """# List Title

- Item 1

- Item 2

- Item 3"""
        
        result = docx2md.fix_markdown_formatting(input_md)
        
        # The list items should not have empty lines between them
        self.assertIn("# List Title\n\n- Item 1\n- Item 2\n- Item 3", result)
        
    def test_complex_list_formatting(self):
        """Test that complex lists with mixed types and nesting have correct formatting."""
        input_md = """# Mixed Lists

- Bullet 1

- Bullet 2

  - Nested bullet 1

  - Nested bullet 2

- Bullet 3

1. Numbered 1

2. Numbered 2

   - Mixed nested bullet

   1. Mixed nested number

3. Numbered 3"""
        
        # Update the expected output to match our formatter's behavior
        # Note: We keep a blank line between bullet lists and numbered lists
        expected = """# Mixed Lists

- Bullet 1
- Bullet 2
  - Nested bullet 1
  - Nested bullet 2
- Bullet 3

1. Numbered 1
2. Numbered 2
   - Mixed nested bullet
   1. Mixed nested number
3. Numbered 3"""
        
        result = docx2md.fix_markdown_formatting(input_md)
        
        # Removed debugging prints
        
        # Convert to normalized form for comparison (remove any double spaces)
        result_normalized = "\n".join([line.rstrip() for line in result.split("\n")])
        expected_normalized = "\n".join([line.rstrip() for line in expected.split("\n")])
        
        self.assertEqual(result_normalized, expected_normalized)


class TestDocxMdCommand(unittest.TestCase):
    """Test the CLI interface with mocked subprocess call."""
    
    @patch('subprocess.run')
    def test_cli_applies_list_formatting(self, mock_run):
        """Test that the CLI applies list formatting to improve readability."""
        # Create a mock return value with CommonMark content that has double-spaced lists
        mock_process = MagicMock()
        mock_process.stdout = "# Title\n\n- Item 1\n\n- Item 2\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Capture stdout to validate the formatting is applied
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['docx2md', 'fake.docx']):
                docx2md.main()
            
            output = fake_out.getvalue()
            # Our formatter should convert double-spaced lists to single-spaced
            self.assertIn("# Title\n\n- Item 1\n- Item 2", output)
    
    @patch('subprocess.run')
    def test_cli_with_line_wrapping(self, mock_run):
        """Test that --wrap enables line wrapping."""
        # Create a mock return value
        mock_process = MagicMock()
        mock_process.stdout = "# Title\n\n- Item 1\n\n- Item 2\n"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Capture stdout to validate correct options are used
        with patch('sys.stdout', new=StringIO()):
            with patch('sys.argv', ['docx2md', '--wrap', '80', 'fake.docx']):
                docx2md.main()
            
            # Check that pandoc was called with correct wrapping options
            # Extract the args that were passed to subprocess.run
            args = mock_run.call_args[0][0]
            
            # Verify wrap options were included
            self.assertIn("--wrap=auto", args)
            self.assertIn("--columns", args)
            self.assertIn("80", args)


if __name__ == '__main__':
    unittest.main()