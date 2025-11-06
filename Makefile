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

# Generate template for a new tool
new-tool:
	@if [ -z "$(name)" ]; then \
		echo "Error: Tool name not specified. Use 'make new-tool name=toolname'"; \
		exit 1; \
	fi
	@echo "Creating new tool: $(name)"
	@mkdir -p $(TOOLS_DIR)/$(name)

	# Create __init__.py
	@touch $(TOOLS_DIR)/$(name)/__init__.py

	# Create Python script template
	@echo '#!/usr/bin/env python3' > $(TOOLS_DIR)/$(name)/$(name).py
	@echo '"""' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '$(name): Description' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo 'Usage: $(name) [options]' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '"""' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo 'import sys' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo 'import argparse' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo 'def main():' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    parser = argparse.ArgumentParser(description="Tool description")' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    parser.add_argument("--version", action="version", version="$(name) 1.0.0")' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    args = parser.parse_args()' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    ' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    # Your code here' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    print("Hello from $(name)")' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    ' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    return 0' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo 'if __name__ == "__main__":' >> $(TOOLS_DIR)/$(name)/$(name).py
	@echo '    sys.exit(main())' >> $(TOOLS_DIR)/$(name)/$(name).py
	@chmod +x $(TOOLS_DIR)/$(name)/$(name).py

	# Create tools.toml config
	@echo '[[tool]]' > $(TOOLS_DIR)/$(name)/tools.toml
	@echo 'command = "$(name)"' >> $(TOOLS_DIR)/$(name)/tools.toml
	@echo 'script = "$(name)/$(name).py"' >> $(TOOLS_DIR)/$(name)/tools.toml
	@echo 'description = "A simple utility"' >> $(TOOLS_DIR)/$(name)/tools.toml
	@echo 'version = "1.0.0"' >> $(TOOLS_DIR)/$(name)/tools.toml
	@echo 'system_dependencies = []' >> $(TOOLS_DIR)/$(name)/tools.toml

	@echo "Created new tool: $(TOOLS_DIR)/$(name)/$(name).py"
	@echo "Created config:   $(TOOLS_DIR)/$(name)/tools.toml"
	@echo ""
	@echo "IMPORTANT: Add the following to pyproject.toml [project.scripts] section:"
	@echo "$(name) = \"tools.$(name).$(name):main\""
	@echo ""
	@echo "Then run: make install"
