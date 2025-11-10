#!/bin/bash
# Install ProtonMail Sync systemd service and timer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing ProtonMail Sync systemd service...${NC}\n"

# Check if protonmail command is available
if ! command -v protonmail &> /dev/null; then
    echo -e "${RED}Error: 'protonmail' command not found in PATH${NC}"
    echo "Please install the protonmail tool first:"
    echo "  cd /data/repos/toolkit"
    echo "  uv tool install --editable ."
    exit 1
fi

# Check if ProtonMail Bridge is installed
if ! command -v protonmail-bridge &> /dev/null && ! command -v proton-bridge &> /dev/null; then
    echo -e "${YELLOW}Warning: ProtonMail Bridge not found${NC}"
    echo "The service will only run when ProtonMail Bridge is running."
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create systemd user directory if it doesn't exist
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

# Copy service and timer files
echo "Copying service files to $SYSTEMD_DIR..."
cp "$SCRIPT_DIR/protonmail-sync.service" "$SYSTEMD_DIR/"
cp "$SCRIPT_DIR/protonmail-sync.timer" "$SYSTEMD_DIR/"

# Create config directory for environment file
CONFIG_DIR="$HOME/.config/protonmail"
mkdir -p "$CONFIG_DIR"

# Check if environment file exists
if [ ! -f "$CONFIG_DIR/env" ]; then
    echo -e "\n${YELLOW}Creating environment configuration file...${NC}"

    # Try to source the existing protonmail.sh if it exists
    if [ -f "$HOME/.bash.d/local/after/protonmail.sh" ]; then
        echo "Found existing ProtonMail configuration, copying credentials..."
        source "$HOME/.bash.d/local/after/protonmail.sh"
        cat > "$CONFIG_DIR/env" <<EOF
# ProtonMail Environment Configuration
PROTONMAIL_USERNAME=${PROTONMAIL_USERNAME:-your-email@protonmail.com}
PROTONMAIL_API_KEY=${PROTONMAIL_API_KEY:-your-bridge-api-key}
DDATA=${DDATA:-$HOME/data}
EOF
    else
        # Copy example file
        cp "$SCRIPT_DIR/protonmail-env.example" "$CONFIG_DIR/env"
        echo -e "${YELLOW}Please edit $CONFIG_DIR/env and add your credentials${NC}"
    fi

    chmod 600 "$CONFIG_DIR/env"
    echo "Created: $CONFIG_DIR/env"
else
    echo -e "${GREEN}Environment file already exists: $CONFIG_DIR/env${NC}"
fi

# Reload systemd daemon
echo -e "\nReloading systemd daemon..."
systemctl --user daemon-reload

# Enable and start the timer
echo "Enabling and starting protonmail-sync.timer..."
systemctl --user enable protonmail-sync.timer
systemctl --user start protonmail-sync.timer

echo -e "\n${GREEN}✓ Installation complete!${NC}\n"
echo "Service status:"
systemctl --user status protonmail-sync.timer --no-pager

echo -e "\n${GREEN}Useful commands:${NC}"
echo "  View timer status:    systemctl --user status protonmail-sync.timer"
echo "  View service logs:    journalctl --user -u protonmail-sync -f"
echo "  List timer schedule:  systemctl --user list-timers protonmail-sync.timer"
echo "  Trigger sync now:     systemctl --user start protonmail-sync.service"
echo "  Stop timer:           systemctl --user stop protonmail-sync.timer"
echo "  Disable timer:        systemctl --user disable protonmail-sync.timer"

echo -e "\n${YELLOW}Note:${NC} The sync will only run when ProtonMail Bridge is running."
echo "Next sync will occur in 5 minutes, or run manually with: systemctl --user start protonmail-sync.service"
