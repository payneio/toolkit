#!/usr/bin/env python3
"""
Browser automation tool powered by browser-use.

This tool allows executing browser automation from command line instructions.
It takes instruction text and uses browser-use to automate browser tasks.
"""

import argparse
import sys
import asyncio
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables for API keys
load_dotenv()

# Import browser-use and related dependencies
try:
    from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig

    # Optional imports for different LLM providers
    openai_available = False
    anthropic_available = False

    try:
        from langchain_openai import ChatOpenAI

        openai_available = True
    except ImportError:
        pass

    try:
        from langchain_anthropic import ChatAnthropic

        anthropic_available = True
    except ImportError:
        pass

except ImportError:
    sys.stderr.write("Error: Required dependencies not found. Install with:\n")
    sys.stderr.write("pip install browser-use python-dotenv\n")
    sys.stderr.write("pip install langchain-openai  # For OpenAI models\n")
    sys.stderr.write("pip install langchain-anthropic  # For Anthropic models\n")
    sys.stderr.write("patchright install chromium\n")
    sys.exit(1)


async def run_browser_task(
    task: str,
    provider: str = "openai",
    model: str = "gpt-4o",
    max_steps: int = 25,
    max_actions_per_step: int = 4,
) -> Dict[str, Any]:
    """
    Run a browser task based on the given instruction.

    Args:
        task: The instruction text describing what to do in the browser
        provider: The model provider to use
        model: The specific model name to use
        max_steps: Maximum number of steps the agent can take
        max_actions_per_step: Maximum number of actions per step

    Returns:
        The result from the browser-use agent
    """
    # Configure the browser (headless mode is required for environments without X11 display)
    browser = Browser(
        config=BrowserConfig(
            headless=True,
            new_context_config=BrowserContextConfig(
                viewport_expansion=0,
            ),
        )
    )

    # Select and configure the appropriate LLM based on provider
    if provider.lower() == "anthropic":
        if not anthropic_available:
            raise ImportError(
                "Anthropic integration not available. Install with: pip install langchain-anthropic"
            )
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        llm = ChatAnthropic(model=model)  # type: ignore
    elif provider.lower() == "openai":
        if not openai_available:
            raise ImportError(
                "OpenAI integration not available. Install with: pip install langchain-openai"
            )
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        llm = ChatOpenAI(model=model)  # type: ignore
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Create and run the agent
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        max_actions_per_step=max_actions_per_step,
    )

    # Execute the task with a maximum number of steps
    result = await agent.run(max_steps=max_steps)
    return result  # type: ignore


def main():
    parser = argparse.ArgumentParser(
        description="Execute browser automation from command line instructions"
    )
    parser.add_argument(
        "instruction", nargs="*", help="Instruction text for browser automation"
    )
    parser.add_argument(
        "--provider",
        "-p",
        choices=["openai", "anthropic"],
        default="openai",
        help="The model provider to use (default: openai)",
    )
    parser.add_argument(
        "--model", "-m", help="The model to use (default depends on provider)"
    )
    parser.add_argument(
        "--file", "-f", help="Read instruction from file instead of command line"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=25,
        help="Maximum number of steps the agent can take (default: 25)",
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=4,
        help="Maximum number of actions per step (default: 4)",
    )

    args = parser.parse_args()

    # Set default model based on provider if not specified
    if not args.model:
        if args.provider == "anthropic":
            args.model = "claude-3-opus-20240229"
        else:  # openai
            args.model = "gpt-4o"

    # Get instruction from file, command line args, or stdin
    if args.file:
        try:
            with open(args.file, "r") as f:
                instruction = f.read().strip()
        except Exception as e:
            sys.stderr.write(f"Error reading file: {e}\n")
            sys.exit(1)
    elif args.instruction:
        instruction = " ".join(args.instruction)
    else:
        # Check if there's input from stdin
        if not sys.stdin.isatty():
            instruction = sys.stdin.read().strip()
        else:
            parser.print_help()
            sys.exit(1)

    if not instruction:
        sys.stderr.write("Error: No instruction provided\n")
        sys.exit(1)

    print(f"Running browser task: {instruction}")
    print(f"Using model: {args.provider}/{args.model}")

    try:
        result = asyncio.run(
            run_browser_task(
                task=instruction,
                provider=args.provider,
                model=args.model,
                max_steps=args.max_steps,
                max_actions_per_step=args.max_actions,
            )
        )
        print("\nTask completed!")
        if "output" in result:
            print(result["output"])
    except Exception as e:
        sys.stderr.write(f"Error executing browser task: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
