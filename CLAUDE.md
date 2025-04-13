# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Build and install tools: `make all` (runs `make build && make bin && make install`)
- Install tool dependencies with `uv`: `make build` 
- Create tool executable: `make bin`
- Install tool executables (symlinks to `~/.local/bin`): `make install`
- Lint code: `make check` or `uvx ruff check`
- Run all tests: `uv run pytest -v`
- Run specific tests: `uv run pytest tests/test_gpt.py -v`
- Run single test: `uv run pytest tests/test_gpt.py::TestGPT::test_generate_text -v`
- Create new tool: `make new-tool name=toolname`

After a tool is installed, it can be used from the command line in any directory.

## Code Style Guidelines
- Imports: Standard library first, then third-party, then local modules. Don't put imports inside blocks, keep them at the top.
- Type annotations: Use type hints for function parameters and return values
- Naming: snake_case for functions/variables, PascalCase for classes
- Documentation: Docstrings with usage examples for all modules/functions
- Comments: Limit comments to explaining the "why" not the "how" or the "what". Make comments proper english and end with a period.
- Linting: Uses ruff for code quality checks
- Error handling: Use specific exceptions with descriptive messages, exit with sys.exit(1)
- Testing: Unittest with heavy mocking, tests prefixed with "test_"
- Configuration: TOML for tool configs with standard fields (command, script, description, version)
- CLI: Use argparse with consistent flag patterns, support stdin/stdout piping
- Follow the Unix philosophy: Each tool does one thing well, text-based interfaces

## Best Practices
- Always prefer `uv add` to `uvx pip install`.
