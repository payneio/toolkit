#!/usr/bin/env python3
import sys
import json
import unittest
from io import StringIO
from unittest.mock import patch
sys.path.append('../tools/echo')
import echo

class TestEcho(unittest.TestCase):
    
    def test_basic_echo(self):
        with patch('sys.argv', ['echo', 'Hello World']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                echo.main()
                self.assertEqual(fake_out.getvalue().strip(), 'Hello World')
    
    def test_uppercase(self):
        with patch('sys.argv', ['echo', '--uppercase', 'Hello World']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                echo.main()
                self.assertEqual(fake_out.getvalue().strip(), 'HELLO WORLD')
    
    def test_json_input(self):
        with patch('sys.argv', ['echo', '--json', '{"message": "Hello World"}']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                echo.main()
                result = json.loads(fake_out.getvalue())
                self.assertEqual(result['echo']['message'], 'Hello World')

if __name__ == '__main__':
    unittest.main()