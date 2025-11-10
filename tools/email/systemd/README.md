# ProtonMail Sync Systemd Service

Automated systemd service and timer to sync ProtonMail emails every 5 minutes when ProtonMail Bridge is running.

## Features

- **Automatic syncing** - Runs every 5 minutes
- **Bridge detection** - Only runs when ProtonMail Bridge is active
- **Resource limits** - Memory and task limits for safety
- **Security hardening** - Restricted file system access
- **User service** - Runs as your user, no root required
- **Logging** - All output logged to systemd journal

## Files

- `protonmail-sync.service` - Systemd service definition
- `protonmail-sync.timer` - Timer to run service every 5 minutes
- `protonmail-env.example` - Environment variable template
- `install.sh` - Installation script
- `README.md` - This file

## Prerequisites

1. **ProtonMail Bridge** must be installed and running
   ```bash
   # Check if bridge is running
   pgrep -f protonmail-bridge
   ```

2. **protonmail tool** must be installed
   ```bash
   # Install from toolkit directory
   uv tool install --editable .

   # Verify installation
   which protonmail
   ```

3. **ProtonMail credentials** configured
   - Username (email address)
   - Bridge API key

## Installation

### Quick Install

```bash
cd systemd
./install.sh
```

The install script will:
1. Copy service files to `~/.config/systemd/user/`
2. Create environment config at `~/.config/protonmail/env`
3. Enable and start the timer
4. Show status and useful commands

### Manual Installation

If you prefer to install manually:

1. **Copy systemd files**
   ```bash
   mkdir -p ~/.config/systemd/user
   cp protonmail-sync.service ~/.config/systemd/user/
   cp protonmail-sync.timer ~/.config/systemd/user/
   ```

2. **Create environment configuration**
   ```bash
   mkdir -p ~/.config/protonmail
   cp protonmail-env.example ~/.config/protonmail/env
   chmod 600 ~/.config/protonmail/env
   ```

3. **Edit environment file**
   ```bash
   nano ~/.config/protonmail/env
   ```

   Add your credentials:
   ```bash
   PROTONMAIL_USERNAME=your-email@protonmail.com
   PROTONMAIL_API_KEY=your-bridge-api-key
   DDATA=/home/yourusername/data
   ```

4. **Enable and start timer**
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable protonmail-sync.timer
   systemctl --user start protonmail-sync.timer
   ```

## Usage

### Check Status

```bash
# Timer status
systemctl --user status protonmail-sync.timer

# Service status
systemctl --user status protonmail-sync.service

# View when next sync will run
systemctl --user list-timers protonmail-sync.timer
```

### View Logs

```bash
# Follow logs in real-time
journalctl --user -u protonmail-sync -f

# View last 50 lines
journalctl --user -u protonmail-sync -n 50

# View logs from today
journalctl --user -u protonmail-sync --since today
```

### Manual Trigger

```bash
# Trigger sync immediately
systemctl --user start protonmail-sync.service

# Watch it run
journalctl --user -u protonmail-sync -f
```

### Stop/Disable

```bash
# Stop timer (won't run automatically)
systemctl --user stop protonmail-sync.timer

# Disable timer (won't start on boot)
systemctl --user disable protonmail-sync.timer

# Re-enable
systemctl --user enable protonmail-sync.timer
systemctl --user start protonmail-sync.timer
```

## How It Works

1. **Timer triggers** every 5 minutes (after boot delay of 1 minute)
2. **Service checks** if ProtonMail Bridge is running
3. **If bridge is active**, runs `protonmail sync`
4. **If bridge is not running**, exits gracefully (logged to journal)
5. **Sync runs** with idempotency - only downloads new emails

## Troubleshooting

### Service fails to start

Check the logs:
```bash
journalctl --user -u protonmail-sync -n 50
```

Common issues:
- ProtonMail Bridge not running
- Environment file missing or incorrect credentials
- `protonmail` command not in PATH

### No new emails syncing

Check if service is running:
```bash
systemctl --user status protonmail-sync.service
```

Trigger manual sync and watch logs:
```bash
systemctl --user start protonmail-sync.service
journalctl --user -u protonmail-sync -f
```

### Change sync frequency

Edit the timer file:
```bash
nano ~/.config/systemd/user/protonmail-sync.timer
```

Change `OnUnitActiveSec=5min` to your desired frequency (e.g., `10min`, `30min`, `1h`)

Then reload:
```bash
systemctl --user daemon-reload
systemctl --user restart protonmail-sync.timer
```

## Security

The service includes several security features:

- **PrivateTmp=yes** - Isolated /tmp directory
- **ProtectSystem=strict** - Read-only system directories
- **ProtectHome=read-only** - Read-only home directory
- **ReadWritePaths** - Only sync directory is writable
- **NoNewPrivileges=yes** - Cannot gain new privileges
- **MemoryMax=512M** - Memory limit
- **TasksMax=50** - Process limit

Environment file permissions are set to `600` (owner read/write only).

## Uninstall

```bash
# Stop and disable timer
systemctl --user stop protonmail-sync.timer
systemctl --user disable protonmail-sync.timer

# Remove systemd files
rm ~/.config/systemd/user/protonmail-sync.{service,timer}

# Remove environment config (optional)
rm ~/.config/protonmail/env

# Reload daemon
systemctl --user daemon-reload
```

## License

Same license as the toolkit project.
