---
command: protonmail
script: email/protonmail.py
description: Access and manage ProtonMail emails via Bridge
version: 1.0.0
category: email
system_dependencies:
- protonmail-bridge
---

# protonmail

Access and manage ProtonMail emails through ProtonMail Bridge. All commands work with local cached `.eml` files for fast, offline access.

## Prerequisites

This tool requires Proton Mail Bridge to be set up and running. Proton Mail Bridge is a GUI app: https://proton.me/mail/bridge

## Installation

```bash
# Install the toolkit
cd /data/repos/toolkit
make install

# Verify installation
which protonmail
```

## Setup

### Credentials

Set environment variables with your ProtonMail Bridge credentials:

```bash
# Add to ~/.bashrc or ~/.profile
export PROTONMAIL_USERNAME=your-email@protonmail.com
export PROTONMAIL_API_KEY=your-bridge-api-key
export DDATA=/data  # optional, defaults to ~/data
```

Then reload your shell or run `source ~/.bashrc`.

## Usage

### Quick Start

```bash
# Sync all emails to local cache
protonmail sync

# List emails from local cache
protonmail list

# Search emails
protonmail search "invoice"

# Read an email by filename
protonmail read "2024-07-17_01-14-40_from_..._.eml"

# Send email (requires IMAP connection)
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

## Automated Syncing

Automatically sync emails every 5 minutes when ProtonMail Bridge is running using the `schedule` tool.

### Setup Automated Sync

```bash
# First, enable linger so timer runs even when logged out
loginctl enable-linger $USER

# Create the timer with inline environment variables
schedule add protonmail-sync \
    --command "protonmail sync" \
    --schedule "5min" \
    --description "Sync ProtonMail emails every 5 minutes" \
    --condition-command "pgrep -f 'protonmail-bridge|proton-bridge'" \
    -e "PROTONMAIL_USERNAME=your-email@protonmail.com" \
    -e "PROTONMAIL_API_KEY=your-bridge-api-key" \
    -e "DDATA=/data"
```

Replace the email and API key with your actual credentials from ProtonMail Bridge.

**Note**: Environment variables are passed inline with `-e` flags because systemd user units don't inherit shell environment variables from ~/.bashrc.

### Management

```bash
# View timer status
schedule status protonmail-sync

# View sync logs in real-time
schedule logs protonmail-sync --follow

# List all timers
schedule list

# Temporarily disable
schedule disable protonmail-sync

# Re-enable
schedule enable protonmail-sync
schedule start protonmail-sync

# Remove completely
schedule remove protonmail-sync
```

### How It Works

1. Timer triggers every 5 minutes (1 minute after boot)
2. Condition command checks if ProtonMail Bridge is running
3. If bridge is active, runs `protonmail sync`
4. Only downloads new emails (idempotent)
5. Logs to systemd journal (view with `schedule logs protonmail-sync`)

## File Organization

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

## Features

- **Fast, offline access** - Read emails without internet
- **Idempotent syncing** - Only downloads new emails
- **Full email preservation** - Complete `.eml` files with headers
- **Search capabilities** - Search by sender or subject
- **Automated backups** - Schedule timer for continuous sync
- **Security** - Systemd service with restricted permissions

## Configuration

The tool uses these environment variables:

- `PROTONMAIL_USERNAME` - Your ProtonMail email address (required)
- `PROTONMAIL_API_KEY` - Bridge API key/password (required)
- `DDATA` - Base data directory (optional, defaults to `~/data`)

Default storage location: `$DDATA/messages/email/protonmail/`
