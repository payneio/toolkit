---
command: gpt
script: gpt/gpt.py
description: A simple OpenAI text generation utility
version: 1.0.0
category: gpt
---

# gpt

Interact with OpenAI's GPT models from the command line. Send prompts and receive AI-generated responses.

## Prerequisites

- OpenAI API key

## Installation

```bash
cd /data/repos/toolkit
make install
which gpt
```

## Setup

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Add to ~/.bashrc or ~/.profile to persist
```

## Usage

### Basic Usage

```bash
# Send a prompt
gpt "Explain quantum computing in simple terms"

# Use specific model
gpt --model gpt-4 "Write a Python function to sort a list"

# Read prompt from file
gpt < prompt.txt

# Interactive mode
echo "What is the capital of France?" | gpt
```

### Options

```bash
gpt [options] "prompt"

Options:
  prompt              Text prompt for GPT (required)
  --model MODEL       GPT model to use (default: gpt-4o-mini)
  --temperature TEMP  Creativity level 0.0-2.0 (default: 0.7)
  --max-tokens NUM    Maximum response length (default: 1000)
  --system PROMPT     System prompt to set behavior
  -h, --help          Show help message
```

## Supported Models

- `gpt-4o` - Most capable, best for complex tasks
- `gpt-4o-mini` - Fast and affordable (default)
- `gpt-4-turbo` - Large context window
- `gpt-4` - High capability
- `gpt-3.5-turbo` - Fast and economical

## Examples

### Simple Questions

```bash
gpt "What is the weather like today?"
gpt "Explain recursion"
```

### Code Generation

```bash
gpt "Write a Python function to calculate fibonacci numbers"
gpt --model gpt-4 "Create a React component for a todo list"
```

### Text Processing

```bash
# Summarize a file
cat article.txt | gpt "Summarize this article in 3 bullet points"

# Translate
echo "Hello world" | gpt "Translate to French"

# Code review
cat script.py | gpt "Review this code and suggest improvements"
```

### With System Prompts

```bash
gpt --system "You are a Python expert" "How do I use asyncio?"
gpt --system "Respond in haiku form" "Describe AI"
```

### Batch Processing

```bash
# Process multiple prompts
for question in "What is AI?" "What is ML?" "What is DL?"; do
    gpt "$question" >> answers.txt
done
```

## Features

- **Multiple models** - Choose from various GPT models
- **Flexible input** - Prompt as argument or from stdin
- **Customizable** - Adjust temperature, tokens, system prompts
- **Pipe-friendly** - Works in Unix pipelines
- **Fast** - Direct API access

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)

## Tips

- Use `gpt-4o-mini` for fast, cheap responses (default)
- Use `gpt-4` or `gpt-4o` for complex reasoning
- Lower temperature (0.1-0.3) for factual responses
- Higher temperature (0.8-1.5) for creative writing
- System prompts help control tone and expertise level

## Cost Considerations

- `gpt-4o-mini` is most economical for general use
- `gpt-4` costs more but provides higher quality
- Limit max-tokens to control costs
- Monitor usage in OpenAI dashboard

## Troubleshooting

### API Key Not Found

```bash
echo $OPENAI_API_KEY  # Should show your key
export OPENAI_API_KEY=sk-...
```

### Rate Limits

If you hit rate limits, wait a moment and retry, or upgrade your OpenAI plan.
