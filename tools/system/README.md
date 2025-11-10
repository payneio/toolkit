# Backup System

Gathers files not in /data into /data/backup

## Configuration

Configuration file located at `~/.config/toolkit/backup-config.json`:

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
backup-collect
```

## Environment Variables

- `DBACKUP`: Main backup directory (default: /data/backup)
- `BACKUP_RETENTION`: Number of backups to keep (overrides config file settings)
