---
command: browser
script: browser/browser.py
description: Browse the web using natural language via browser-use
version: 1.0.0
category: browser
---

# browser

Browser automation tool powered by browser-use. Execute browser tasks from the command line using natural language instructions.

## Prerequisites

- **LLM Provider** - Requires API key for OpenAI or Anthropic
- **Chromium/Chrome** - Used by the automation framework

## Installation

```bash
# Install the toolkit
cd /data/repos/toolkit
make install

# Verify installation
which browser
```

## Setup

### API Key Configuration

Set up your LLM provider API key:

```bash
# For OpenAI
export OPENAI_API_KEY=sk-...

# For Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Add to ~/.bashrc or ~/.profile to persist
```

## Usage

### Basic Usage

```bash
# Execute a browser task
browser "Go to google.com and search for python tutorials"

# Use specific LLM provider
browser --model gpt-4 "Fill out the contact form on example.com"
browser --model claude-3-5-sonnet "Take a screenshot of the homepage"
```

### Options

```bash
browser [options] "instruction"

Options:
  instruction              Natural language instruction for browser task (required)
  --model MODEL            LLM model to use (default: gpt-4o-mini)
  --headless              Run browser in headless mode (no visible window)
  --timeout SECONDS       Maximum time for task execution (default: 300)
  -h, --help              Show help message
```

## Supported Models

### OpenAI Models
- `gpt-4o` - Most capable, best for complex tasks
- `gpt-4o-mini` - Fast and affordable (default)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### Anthropic Models
- `claude-3-5-sonnet-20241022` - Most capable
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

## Examples

### Web Search

```bash
browser "Search Google for 'best python libraries 2024' and summarize the top 3 results"
```

### Form Filling

```bash
browser "Go to example.com/contact and fill in the form with: Name: John Doe, Email: john@example.com, Message: Testing automation"
```

### Screenshots

```bash
browser "Navigate to github.com and take a screenshot"
```

### Data Extraction

```bash
browser "Go to news.ycombinator.com and list the top 5 post titles"
```

### Multi-step Tasks

```bash
browser "Go to amazon.com, search for 'wireless mouse', filter by 4+ stars, and show me the top 3 results with prices"
```

## Features

- **Natural language control** - Use plain English to automate browser tasks
- **AI-powered** - Uses LLMs to understand and execute complex instructions
- **Multi-step workflows** - Handle complex sequences of actions
- **Screenshot capture** - Can take screenshots as part of tasks
- **Form filling** - Automatically fill out forms
- **Data extraction** - Extract information from web pages
- **Headless mode** - Run without visible browser window

## Environment Variables

- `OPENAI_API_KEY` - API key for OpenAI models
- `ANTHROPIC_API_KEY` - API key for Anthropic Claude models

## Notes

- Tasks are executed using browser automation via browser-use
- Complex tasks may take longer to complete
- Headless mode is faster but you won't see the browser actions
- Some websites may block automation (check robots.txt)
- API costs apply based on model usage
- Default timeout is 5 minutes; adjust with `--timeout` for longer tasks

## Troubleshooting

### API Key Not Found

```bash
# Ensure API key is exported
echo $OPENAI_API_KEY
# or
echo $ANTHROPIC_API_KEY

# Add to shell config if missing
export OPENAI_API_KEY=sk-...
```

### Browser Launch Fails

Ensure Chromium or Chrome is installed on your system. The browser-use library will try to find it automatically.

### Timeout Errors

For complex tasks, increase the timeout:

```bash
browser --timeout 600 "complex long-running task"
```
