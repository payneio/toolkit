# Toolkit Project Makefile

.PHONY: all install install-links build check clean bin new-tool

# Directory paths
REPO_DIR := $(shell pwd)
BIN_DIR := $(REPO_DIR)/bin
TOOLS_DIR := $(REPO_DIR)/tools
TARGET_BIN_DIR := $(HOME)/.local/bin
TARGET_MAN_DIR := $(HOME)/.local/share/man/man1

# Find all tools.toml files
TOOLS_TOML := $(shell find $(TOOLS_DIR) -name "tools.toml")

# Default target
all: build bin install

# Install links
install: install-links

# Install symlinks to tools in ~/.local/bin
install-links:
	@echo "Setting up scripts in $(TARGET_BIN_DIR)"
	@echo "=================================="
	@mkdir -p $(TARGET_BIN_DIR)
	@find $(BIN_DIR) -type f -executable | while read file; do \
		filename=$$(basename $$file); \
		echo "Creating symlink for $$filename"; \
		ln -sf $$file $(TARGET_BIN_DIR)/$$filename; \
	done
	@echo "Symlinks created in $(TARGET_BIN_DIR)"
	@echo "Make sure $(TARGET_BIN_DIR) is in your PATH, e.g.:"
	@echo "export PATH=\"$(HOME)/.local/bin:\$$PATH\""

# Man pages have been removed from this project

# Build - run uv sync to ensure all dependencies are up to date
build:
	@echo "Syncing dependencies with UV"
	uv sync --all-groups

# Run linting checks
check:
	@echo "Running Ruff checks..."
	uvx ruff check

# Generate bin launcher scripts from tools.toml files
bin:
	@echo "Generating bin launcher scripts..."
	@mkdir -p $(BIN_DIR)
	@mkdir -p templates
	@for toml in $(TOOLS_TOML); do \
		category=$$(basename $$(dirname $$toml)); \
		echo "Processing $$category tools..."; \
		grep -A10 '^\[\[tool\]\]' $$toml | while IFS= read -r line; do \
			case "$$line" in \
				*"command ="*) \
					cmd=$$(echo "$$line" | sed -E 's/command *= *"?([^"]*)"?/\1/') \
					;; \
				*"script ="*) \
					script=$$(echo "$$line" | sed -E 's/script *= *"?([^"]*)"?/\1/'); \
					if [ ! -z "$$cmd" ] && [ ! -z "$$script" ]; then \
						echo "Creating bin launcher for $$cmd"; \
						cat templates/bin_launcher.sh.template | sed "s|{{TOOL_SCRIPT}}|$$script|g" > "$(BIN_DIR)/$$cmd"; \
						chmod +x "$(BIN_DIR)/$$cmd"; \
						cmd=""; script=""; \
					fi \
					;; \
			esac; \
		done; \
	done
	@echo "Bin launcher scripts generated."

# Clean up generated files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "Cleanup complete."

# Generate template for a new tool
new-tool:
	@if [ -z "$(name)" ]; then \
		echo "Error: Tool name not specified. Use 'make new-tool name=toolname'"; \
		exit 1; \
	fi
	@echo "Creating new tool: $(name)"
	@mkdir -p $(TOOLS_DIR)/$(name)
	
	# Create templates directory if it doesn't exist
	@mkdir -p templates
	
	# Create Python script template
	@echo "#!/usr/bin/env python3\n\"\"\"\n$(name): Description\n\nUsage: $(name) [options]\n\"\"\"\nimport sys\nimport argparse\n\ndef main():\n    parser = argparse.ArgumentParser(description=\"Tool description\")\n    parser.add_argument('--version', action='version', version='$(name) 1.0.0')\n    args = parser.parse_args()\n    \n    # Your code here\n    print(\"Hello from $(name)\")\n    \n    return 0\n\nif __name__ == \"__main__\":\n    sys.exit(main())" > $(TOOLS_DIR)/$(name)/$(name).py
	@chmod +x $(TOOLS_DIR)/$(name)/$(name).py
	
	# Create tools.toml config
	@echo "[tool]\ncommand = \"$(name)\"\nscript = \"$(name)/$(name).py\"\ndescription = \"A simple utility\"\nversion = \"1.0.0\"\nsystem_dependencies = []" > $(TOOLS_DIR)/$(name)/tools.toml
	
	@echo "Created new tool: $(TOOLS_DIR)/$(name)/$(name).py"
	@echo "Created config:   $(TOOLS_DIR)/$(name)/tools.toml"
	
	# Generate bin launcher
	@$(MAKE) bin
	
	@echo "New tool '$(name)' created successfully."
	@echo "Edit $(TOOLS_DIR)/$(name)/$(name).py to implement your tool."
	@echo "To install: make install"