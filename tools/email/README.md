# Email

## ProtonMail Tool

Access and manage ProtonMail emails through ProtonMail Bridge. All commands work with local cached `.eml` files for fast, offline access.

### Prerequisites

This tool requires Proton Mail Bridge to be set up and running. Proton Mail Bridge is a GUI app: https://proton.me/mail/bridge

### Installation

```bash
# Install the tool
uv tool install --editable .

# Verify installation
which protonmail
```

### Setup Credentials

Create environment file with your ProtonMail Bridge credentials:

```bash
# Option 1: Use existing bash config
# If you have ~/.bash.d/local/after/protonmail.sh, it will be used automatically

# Option 2: Create config manually
mkdir -p ~/.config/protonmail
cat > ~/.config/protonmail/env <<EOF
PROTONMAIL_USERNAME=your-email@protonmail.com
PROTONMAIL_API_KEY=your-bridge-api-key
DDATA=/data
EOF
chmod 600 ~/.config/protonmail/env
```

### Quick Start

```bash
# Sync all emails to local cache (default: $DDATA/messages/email/protonmail)
protonmail sync

# List emails from local cache
protonmail list

# Search emails
protonmail search "invoice"

# Read an email by filename
protonmail read "2024-07-17_01-14-40_from_..._.eml"

# Send email (requires IMAP)
protonmail send
```

### Commands

**Local Cache Commands** (work offline):
- `protonmail sync` - Download all emails to local cache
- `protonmail list [folder]` - List emails from cache
- `protonmail read <filename>` - Read email from cache
- `protonmail search <query>` - Search emails in cache

**IMAP Commands** (require Bridge connection):
- `protonmail send` - Send new email interactively

### Automated Syncing with systemd

Automatically sync emails every 5 minutes when ProtonMail Bridge is running.

#### Install systemd Service

```bash
cd tools/email/systemd
./install.sh
```

The installation will:
1. Install systemd service and timer to `~/.config/systemd/user/`
2. Create environment config at `~/.config/protonmail/env`
3. Enable and start the timer
4. Show status and useful commands

#### Systemd Commands

```bash
# View timer status
systemctl --user status protonmail-sync.timer

# View sync logs
journalctl --user -u protonmail-sync -f

# Trigger sync manually
systemctl --user start protonmail-sync.service

# Stop automatic syncing
systemctl --user stop protonmail-sync.timer

# Disable timer (won't start on boot)
systemctl --user disable protonmail-sync.timer
```

#### How It Works

1. Timer triggers every 5 minutes (1 minute after boot)
2. Service checks if ProtonMail Bridge is running
3. If bridge is active, runs `protonmail sync`
4. Only downloads new emails (idempotent)
5. Logs to systemd journal

See [systemd/README.md](systemd/README.md) for detailed documentation.

### File Organization

Emails are stored as `.eml` files in folder-based directories:

```
$DDATA/messages/email/protonmail/
├── INBOX/
│   └── 2024-07-17_01-14-40_from_customer_example.com_to_you_example.com_Subject.eml
├── Sent/
├── Trash/
├── Folders_transaction/
└── ...
```

Filename format: `YYYY-MM-DD_HH-MM-SS_from_SENDER_to_RECIPIENT_SUBJECT.eml`

### Features

- **Fast, offline access** - Read emails without internet
- **Idempotent syncing** - Only downloads new emails
- **Full email preservation** - Complete `.eml` files with headers
- **Search capabilities** - Search by sender or subject
- **Automated backups** - systemd timer for continuous sync
- **Security hardening** - systemd service with restricted permissions
