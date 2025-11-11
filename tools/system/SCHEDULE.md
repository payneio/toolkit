# schedule

A tool to easily create, manage, and monitor systemd user timers and services following best practices.

## Overview

`schedule` simplifies the management of systemd user timers by providing a simple command-line interface to create timer/service pairs that execute bash commands on a schedule. It handles all the boilerplate configuration and follows systemd best practices for security and resource management.

## Installation

Install the toolkit:

```bash
cd /data/repos/toolkit
make install
```

The `schedule` command will be available in your PATH.

### Enable Linger (Optional but Recommended)

By default, systemd user units only run while you're logged in. To allow timers to run even when you're logged out, enable linger:

```bash
loginctl enable-linger $USER
```

This is essential for timers that should run 24/7, like automated sync jobs.

## Features

- **Easy timer creation** - Create timers with a single command
- **Multiple schedule types** - Support for interval-based and calendar-based schedules
- **Environment variables** - Support for environment files and inline variables
- **Pre-conditions** - Run commands only when conditions are met
- **Security hardening** - Automatic security settings (NoNewPrivileges, PrivateTmp)
- **Log management** - Easy access to service logs via journalctl
- **Status monitoring** - Check timer and service status

## Usage

### List timers

Show all active user timers:

```bash
schedule list
```

Show all timers including inactive ones:

```bash
schedule list --all
```

### Add a timer

Basic timer that runs every 5 minutes:

```bash
schedule add my-task \
    --command "echo 'Hello, World!'" \
    --schedule "5min"
```

Daily backup at 2 AM:

```bash
schedule add daily-backup \
    --command "backup run" \
    --schedule "daily" \
    --on-calendar "*-*-* 02:00:00" \
    --description "Daily backup job"
```

ProtonMail sync with environment file and condition:

```bash
schedule add protonmail-sync \
    --command "protonmail sync" \
    --schedule "5min" \
    --description "Sync ProtonMail emails" \
    --env-file ~/.config/protonmail/env \
    --condition-command "pgrep -f protonmail-bridge"
```

With environment variables:

```bash
schedule add my-task \
    --command "my-script.sh" \
    --schedule "1hour" \
    --environment "API_KEY=secret123" \
    --environment "LOG_LEVEL=debug" \
    --working-directory "/home/user/projects"
```

### Check status

View timer and service status:

```bash
schedule status protonmail-sync
```

This shows:
- Timer status (active/inactive)
- Service status (last run, next run)
- Next scheduled execution time

### View logs

Follow logs in real-time:

```bash
schedule logs protonmail-sync --follow
```

Show last 50 lines:

```bash
schedule logs protonmail-sync --lines 50
```

Show logs since today:

```bash
schedule logs protonmail-sync --since today
```

### Start/Stop timers

Start a timer:

```bash
schedule start protonmail-sync
```

Stop a timer:

```bash
schedule stop protonmail-sync
```

### Enable/Disable timers

Enable timer (start on boot):

```bash
schedule enable protonmail-sync
```

Disable timer (don't start on boot):

```bash
schedule disable protonmail-sync
```

### Remove a timer

Remove timer and service files:

```bash
schedule remove protonmail-sync
```

Remove but keep logs:

```bash
schedule remove protonmail-sync --keep-logs
```

## Schedule Formats

### Interval-based schedules

Use simple time units:

- `5min` - Every 5 minutes
- `1hour` or `1h` - Every hour
- `30min` - Every 30 minutes
- `1day` or `1d` - Every day
- `1week` or `1w` - Every week
- `hourly` - Every hour (alias for 1hour)
- `daily` - Every day (alias for 1day)

### Calendar-based schedules

Use systemd calendar syntax with `--on-calendar`:

- `*-*-* 02:00:00` - Every day at 2 AM
- `Mon *-*-* 09:00:00` - Every Monday at 9 AM
- `*-*-01 00:00:00` - First day of each month at midnight
- `*-*-* *:00:00` - Every hour on the hour

## Advanced Options

### Add command options

- `--name` - Name of the timer/service (required)
- `--command` - Bash command to execute (required)
- `--schedule` - Schedule format (required)
- `--description` - Human-readable description
- `--env-file` - Path to environment file to source
- `--environment` / `-e` - Set environment variable (KEY=VALUE)
- `--condition-command` - Command that must succeed before running
- `--working-directory` - Working directory for the command
- `--on-boot-sec` - Delay after boot (default: 1min)
- `--on-calendar` - Override with calendar-based schedule
- `--persistent` - Run missed timers if system was offline
- `--force` - Overwrite existing timer/service
- `--no-enable` - Don't enable the timer
- `--no-start` - Don't start the timer

## Examples

### ProtonMail Sync

```bash
schedule add protonmail-sync \
    --command "protonmail sync" \
    --schedule "5min" \
    --description "Sync ProtonMail emails every 5 minutes" \
    --env-file ~/.config/protonmail/env \
    --condition-command "pgrep -f protonmail-bridge"
```

### Daily Backup

```bash
schedule add daily-backup \
    --command "backup run --full" \
    --schedule "daily" \
    --on-calendar "*-*-* 02:00:00" \
    --description "Daily backup at 2 AM" \
    --environment "BACKUP_DIR=/mnt/backups"
```

### Hourly Data Sync

```bash
schedule add data-sync \
    --command "rsync -av /source/ /dest/" \
    --schedule "hourly" \
    --description "Sync data every hour" \
    --working-directory "/home/user/sync"
```

### Git Auto-Commit

```bash
schedule add git-autocommit \
    --command "git add -A && git commit -m 'Auto-commit' && git push" \
    --schedule "15min" \
    --description "Auto-commit and push changes" \
    --working-directory "/home/user/projects/myrepo"
```

## File Locations

Timer and service files are stored in:

```
~/.config/systemd/user/
├── <name>.service
└── <name>.timer
```

## Security Features

All services created by `schedule` include:

- `NoNewPrivileges=yes` - Cannot gain new privileges
- `PrivateTmp=yes` - Isolated /tmp directory
- Proper PATH configuration
- Journal logging for stdout/stderr

## Troubleshooting

### Timer not running

Check if the timer is enabled and active:

```bash
schedule status <name>
```

### Service failing

View the logs to see what went wrong:

```bash
schedule logs <name> --lines 50
```

### Command not found

Ensure the command is in the PATH or use an absolute path:

```bash
schedule add my-task \
    --command "/usr/local/bin/my-script" \
    --schedule "5min"
```

### Environment variables not working

Use an environment file:

```bash
# Create env file
echo "API_KEY=secret" > ~/.config/myapp/env
chmod 600 ~/.config/myapp/env

# Use it
schedule add my-task \
    --command "my-script" \
    --schedule "5min" \
    --env-file ~/.config/myapp/env
```

## Comparison with Manual Setup

Instead of manually creating:

1. `.service` file with proper configuration
2. `.timer` file with scheduling
3. Running `systemctl --user daemon-reload`
4. Running `systemctl --user enable <name>.timer`
5. Running `systemctl --user start <name>.timer`

You can do it all with one command:

```bash
schedule add <name> --command "<cmd>" --schedule "<schedule>"
```

## See Also

- `man systemd.timer` - systemd timer documentation
- `man systemd.service` - systemd service documentation
- `man systemd.time` - systemd time specification
- `journalctl` - Query systemd journal

## Important Notes

### Environment Variables

**Critical**: Systemd user units do NOT inherit environment variables from your shell (e.g., ~/.bashrc). Variables set with `export` in your shell will not be available to services.

To make environment variables available to your scheduled commands, pass them inline when creating the timer:

```bash
schedule add my-task \
    --command "my-script" \
    --schedule "1hour" \
    --environment "API_KEY=secret123" \
    --environment "DATABASE_URL=postgres://localhost/mydb"
```

You can also use the `-e` shorthand:

```bash
schedule add my-task \
    --command "my-script" \
    --schedule "1hour" \
    -e "API_KEY=secret123" \
    -e "DATABASE_URL=postgres://localhost/mydb"
```

### User vs System Units

This tool creates **user** systemd units (`systemctl --user`), not system units. User units:

- Run as your user (no root required)
- Stored in `~/.config/systemd/user/`
- Only run while you're logged in (unless linger is enabled)
- Have access to your user's files and permissions

To enable timers to run 24/7 even when logged out:

```bash
loginctl enable-linger $USER
```

## License

Same license as the toolkit project.
