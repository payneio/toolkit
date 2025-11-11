---
command: backup-collect
script: system/backup-collect.py
description: Collect files from various sources into backup directory
version: 1.0.0
category: system
system_dependencies:
- rsync
---

# backup-collect

Collect system information and configuration files for backup purposes.

## Installation

```bash
cd /data/repos/toolkit
make install
which backup-collect
```

## Usage

```bash
# Collect system information
backup-collect

# Specify output directory
backup-collect -o /path/to/backup

# Collect specific categories
backup-collect --category config
backup-collect --category packages
```

### Options

```bash
backup-collect [options]

Options:
  -o, --output DIR    Output directory for collected data
  --category CAT      Collect specific category (config, packages, system)
  -v, --verbose       Enable verbose output
  -h, --help          Show help message
```

## What It Collects

### System Information
- OS version and details
- Kernel information
- Hardware details
- System uptime

### Configuration Files
- User dotfiles (.bashrc, .vimrc, etc.)
- Application configs
- SSH keys (with permissions preserved)
- Custom scripts

### Package Lists
- Installed system packages
- Python packages
- npm packages
- Other package managers

## Features

- **Comprehensive** - Collects essential system data
- **Organized** - Structured output directory
- **Safe** - Preserves permissions
- **Selective** - Choose what to collect
- **Portable** - Outputs in standard formats

## Examples

### Full Backup

```bash
backup-collect -o ~/backups/system-$(date +%Y%m%d)
```

### Scheduled Backup

```bash
# Weekly system backup
schedule add system-backup \
    --command "backup-collect -o /mnt/backups/system-\$(date +\%Y\%m\%d)" \
    --schedule "weekly" \
    --on-calendar "Sun 02:00:00"
```

### Selective Collection

```bash
# Only collect configs
backup-collect --category config -o ~/configs

# Only package lists
backup-collect --category packages -o ~/packages
```

## Output Structure

```
backup-directory/
├── system/
│   ├── os-release
│   ├── kernel-version
│   └── hardware-info
├── config/
│   ├── dotfiles/
│   ├── ssh/
│   └── app-configs/
└── packages/
    ├── apt-packages.txt
    ├── pip-packages.txt
    └── npm-packages.txt
```

## Use Cases

- **System migration** - Document current setup
- **Disaster recovery** - Quick system restoration
- **Configuration management** - Track system changes
- **Compliance** - Document installed software
- **Development** - Share development environment setup

## Notes

- Does not collect sensitive data by default
- SSH keys are collected but not passwords
- Large files are skipped
- Runs without root (collects what's accessible)
- Safe to run frequently
