# Toolkit Project Makefile

.PHONY: all install uninstall build check test clean new-tool

# Directory paths
TOOLS_DIR := tools

# Default target - build and install with uv
all: build install

# Install tools using uv tool install
install:
	@echo "Installing toolkit with uv..."
	uv tool install --editable .
	@echo ""
	@echo "All tools installed successfully!"
	@echo "Tools are now available in your PATH."

# Uninstall tools
uninstall:
	@echo "Uninstalling toolkit..."
	uv tool uninstall toolkit

# Build - sync dependencies with UV
build:
	@echo "Syncing dependencies with UV..."
	uv sync

# Run linting checks
check:
	@echo "Running Ruff checks..."
	uvx ruff check

# Run tests
test:
	@echo "Running tests..."
	uv run pytest -v

# Clean up generated files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete."
