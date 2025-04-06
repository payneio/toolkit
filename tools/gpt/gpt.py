#!/usr/bin/env python3
"""
gpt: A simple OpenAI text generation utility

Generates text using OpenAI's GPT models based on user prompts.

Usage: gpt [options] [prompt]

Examples:
  gpt "Write a haiku about programming"     # Generate text from prompt
  gpt -m gpt-4 "Explain quantum computing"  # Use specific model
  cat prompt.txt | gpt                      # Read prompt from stdin
  gpt -t 0.7 "Write creative story"         # Adjust temperature
"""
import sys
import os
import json
import argparse
import openai
from typing import Optional, Dict, Any

# Default settings
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500

def get_api_key() -> Optional[str]:
    """Get OpenAI API key from environment or config file."""
    # First check environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # Then check config file
    config_paths = [
        os.path.expanduser("~/.config/openai/config.json"),
        os.path.expanduser("~/.openai/config.json"),
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    config = json.load(f)
                    if "api_key" in config:
                        return config["api_key"]
            except (json.JSONDecodeError, IOError):
                pass
    
    return None

def generate_text(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    """Generate text using OpenAI's API."""
    api_key = get_api_key()
    if not api_key:
        sys.stderr.write("Error: OpenAI API key not found.\n")
        sys.stderr.write("Please set OPENAI_API_KEY environment variable or configure it in ~/.config/openai/config.json\n")
        sys.exit(1)
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

def main():
    """Main function to parse arguments and generate text."""
    parser = argparse.ArgumentParser(
        description="Generate text using OpenAI's GPT models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    
    parser.add_argument('prompt', nargs='?', help="The prompt for text generation (default: reads from stdin)")
    parser.add_argument('-m', '--model', default=DEFAULT_MODEL, 
                        help=f"The GPT model to use (default: {DEFAULT_MODEL})")
    parser.add_argument('-t', '--temperature', type=float, default=DEFAULT_TEMPERATURE,
                        help=f"Temperature for text generation (default: {DEFAULT_TEMPERATURE})")
    parser.add_argument('-n', '--max-tokens', type=int, default=DEFAULT_MAX_TOKENS,
                        help=f"Maximum tokens in the response (default: {DEFAULT_MAX_TOKENS})")
    parser.add_argument('-j', '--json', action='store_true',
                        help="Output result as JSON")
    parser.add_argument('-v', '--version', action='version', version='gpt 1.0.0')
    
    args = parser.parse_args()
    
    # Read from stdin or argument
    if args.prompt:
        prompt = args.prompt
    else:
        prompt = sys.stdin.read().strip()
        if not prompt:
            parser.print_help()
            sys.exit(1)
    
    # Generate text
    result = generate_text(
        prompt=prompt,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    # Output results
    if args.json:
        json.dump({"prompt": prompt, "result": result}, sys.stdout)
    else:
        print(result)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())