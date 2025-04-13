#!/usr/bin/env python3
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
from io import StringIO

sys.path.append('./tools/gpt')
import gpt

class TestGPT(unittest.TestCase):
    
    @patch('gpt.get_api_key')
    @patch('openai.OpenAI')
    def test_generate_text(self, mock_openai, mock_get_api_key):
        # Setup mock
        mock_get_api_key.return_value = "fake-api-key"
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is a mock response from GPT."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the function
        result = gpt.generate_text("Test prompt", "gpt-3.5-turbo", 0.7, 500)
        
        # Check results
        self.assertEqual(result, "This is a mock response from GPT.")
        mock_openai.assert_called_once_with(api_key="fake-api-key")
        mock_client.chat.completions.create.assert_called_once()

    @patch('gpt.generate_text')
    def test_main_with_argument(self, mock_generate_text):
        # Setup mock
        mock_generate_text.return_value = "Generated text response"
        
        # Test with command line arguments
        with patch('sys.argv', ['gpt', 'Test prompt']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                gpt.main()
                self.assertEqual(fake_out.getvalue().strip(), "Generated text response")
        
        # Check the mock was called correctly
        mock_generate_text.assert_called_once_with(
            prompt="Test prompt", 
            model="gpt-3.5-turbo", 
            temperature=0.7, 
            max_tokens=500
        )
    
    @patch('gpt.generate_text')
    def test_main_with_json_output(self, mock_generate_text):
        # Setup mock
        mock_generate_text.return_value = "Generated text response"
        
        # Test with JSON output option
        with patch('sys.argv', ['gpt', '-j', 'Test prompt']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                gpt.main()
                output = json.loads(fake_out.getvalue())
                self.assertEqual(output["prompt"], "Test prompt")
                self.assertEqual(output["result"], "Generated text response")

if __name__ == '__main__':
    unittest.main()