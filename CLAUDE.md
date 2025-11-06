# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Build and install tools: `make all` (installs with uv tool install)
- Install tools: `make install` or `uv tool install --editable .`
- Uninstall tools: `make uninstall` or `uv tool uninstall toolkit`
- Sync dependencies: `make build` or `uv sync`
- Lint code: `make check` or `uvx ruff check`
- Run all tests: `make test` or `uv run pytest -v`
- Run specific tests: `uv run pytest tests/test_gpt.py -v`
- Run single test: `uv run pytest tests/test_gpt.py::TestGPT::test_generate_text -v`
- Create new tool: `toolkit create toolname` or `toolkit create toolname --category document` (auto-updates pyproject.toml)

After tools are installed with `uv tool install`, they are available system-wide in your PATH.

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
