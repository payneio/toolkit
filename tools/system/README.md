# System Tools

System administration and automation tools.

## Tools

### [schedule](SCHEDULE.md)

Manage systemd user timers and services. Create, manage, and monitor scheduled tasks using systemd.

**Quick start:**
```bash
# Create a timer
schedule add my-task \
    --command "echo hello" \
    --schedule "5min"

# Manage timers
schedule list
schedule status my-task
schedule logs my-task --follow
```

See [SCHEDULE.md](SCHEDULE.md) for full documentation.

### [backup-collect](backup_collect.md)

Collect system information and configuration files for backup.

**Quick start:**
```bash
backup-collect -o ~/backups/system-$(date +%Y%m%d)
```

See [backup_collect.md](backup_collect.md) for full documentation.

## Common Workflows

### Scheduled Backups

```bash
# Daily system info collection
schedule add daily-backup \
    --command "backup-collect -o /mnt/backups/system-\$(date +\%Y\%m\%d)" \
    --schedule "daily" \
    --on-calendar "*-*-* 02:00:00"
```

### Recurring Tasks

```bash
# Run cleanup every hour
schedule add cleanup \
    --command "/path/to/cleanup.sh" \
    --schedule "1hour"

# Run sync every 5 minutes
schedule add sync \
    --command "rsync -av source/ dest/" \
    --schedule "5min"
```
