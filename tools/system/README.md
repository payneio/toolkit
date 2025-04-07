# Backup System

A comprehensive two-phase backup system that efficiently backs up critical files locally and to external media.

## Overview

The backup system operates in two phases:

1. **Collection Phase**: Gathers files not in /data (like ~/.config, ~/env.sh) into /data/backup
2. **External Backup Phase**: Transfers the entire /data directory (including /data/backup) to external media

This design optimizes for different storage characteristics, particularly for external drives that perform poorly with many small files.

## Tools

The backup system consists of four tools:

1. **backup**: Meta-command that runs both backup phases
2. **backup-collect**: Gathers files into the backup directory
3. **backup-external**: Transfers backups to external media
4. **backup-restore**: Restores files from backups

## Configuration

All tools share a common configuration file located at `~/.config/toolkit/backup-config.json`:

```json
{
  "sources": [
    {
      "name": "config",
      "paths": ["~/.config", "~/env.sh"],
      "exclusions": ["~/.config/Code/Cache/*"]
    }
  ],
  "external": {
    "destinations": [
      {
        "name": "t9_drive",
        "path": "/media/payne/T9/backups",
        "priority": 1
      },
      {
        "name": "backup_mount",
        "path": "/mnt/backup",
        "priority": 2
      }
    ]
  },
  "retention": {
    "local": 7,
    "external": 5
  },
  "schedule": {
    "incremental": "daily",
    "full": "weekly",
    "external": "weekly"
  }
}
```

## Basic Usage

### Creating Backups

```bash
# Run both backup phases
backup

# Only run the local backup phase
backup --local-only

# Only run the external backup phase
backup --external-only

# Perform a full backup instead of incremental
backup --full
```

### Restoring from Backups

```bash
# List available backups
backup-restore --list

# List available external backups
backup-restore --source external --list

# Restore a specific file from local backup
backup-restore --source local --set data --date 2025-04-06_12-34-56 --path /data/projects/report.txt

# Restore a directory from external backup
backup-restore --source external --set config --date 2025-04-01 --path ~/.config/toolkit
```

## Environment Variables

- `DBACKUP`: Main backup directory (default: /data/backup)
- `BACKUP_RETENTION`: Number of backups to keep (overrides config file settings)

## Setting Up Scheduled Backups

To schedule backups with cron, add the following to your crontab:

```bash
# Run daily incremental backup at 1:00 AM
0 1 * * * /home/payne/.local/bin/backup --local-only

# Run full backup and external transfer every Sunday at 2:00 AM
0 2 * * 0 /home/payne/.local/bin/backup --full
```

## Restoration Guide

In case of system failure, follow these steps to restore your system:

1. Install the operating system
2. Install basic tools: `sudo apt install rsync tar`
3. Download and install toolkit
4. Restore configuration files:
   ```bash
   backup-restore --source external --set config --date YYYY-MM-DD --path ~/.config
   backup-restore --source external --set config --date YYYY-MM-DD --path ~/env.sh
   ```
5. Restore data directory:
   ```bash
   backup-restore --source external --set data --date YYYY-MM-DD --path /data
   ```

## Troubleshooting

- **Backup Fails**: Check disk space and file permissions
- **External Drive Not Detected**: Check if drive is mounted properly
- **Restoration Fails**: Make sure target directory is writable