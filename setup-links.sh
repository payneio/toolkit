#!/usr/bin/env bash
# Create symlinks to all utilities in ~/.local/bin

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME/.local/bin"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

echo "Setting up scripts in $TARGET_DIR"
echo "=================================="

# Find all executable files in the bin directory
find "$SCRIPT_DIR/bin" -type f -executable | while read -r file; do
    filename=$(basename "$file")
    echo "Creating symlink for $filename"
    ln -sf "$file" "$TARGET_DIR/$filename"
done

# Verify that the tools can find the repo
echo ""
echo "Testing symlinks..."
for script in "$TARGET_DIR/my-echo" "$TARGET_DIR/scripts-help"; do
    if [[ -f "$script" ]]; then
        # Test with --version which should now be supported by all scripts
        if "$script" --version &>/dev/null; then
            echo "✓ $script works correctly"
        else
            echo "✗ $script not working correctly"
            echo "  This may be due to symlink resolution issues."
            echo "  Try running with --debug flag to see detailed path information:"
            echo "  $script --debug"
            echo ""
            echo "  If needed, you can always use the commands directly from the repo:"
            echo "  cd $SCRIPT_DIR && ./bin/$(basename "$script")"
        fi
    fi
done

echo ""
echo "Symlinks created in $TARGET_DIR"
echo "Make sure $TARGET_DIR is in your PATH, e.g.:"
echo "export PATH=\"$HOME/.local/bin:\$PATH\""
