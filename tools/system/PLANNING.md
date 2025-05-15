# Backup System Planning

This document outlines a comprehensive approach to creating a robust backup system with two distinct phases.

## Overview

The backup system will operate in two phases:

1. **Collection Phase**: Gather files from various source locations into the central `$DBACKUP` directory
2. **External Backup Phase**: Transfer collected backups to external media (e.g., `/media/payne/T9`)

## Critical Backup Sources

The system will focus on backing up these essential locations:

1. **$DDATA Directory** (`/home/payne/data` → symlink to `/data`)

   - Contains most critical user data
   - Likely large in size, requiring incremental backup approach
   - May contain subdirectories that need exclusion rules

2. **Configuration Files**

   - `~/.config` directory - Contains application settings
   - `~/env.sh` - Environment configuration
   - `~/.secrets`

3. Future additions as needed

## Collection Phase

### Goals

- Efficiently gather files from multiple sources
- Maintain directory structure when appropriate
- Handle large files and directories with minimal overhead
- Support incremental backups to reduce bandwidth and storage

### Implementation Approach

#### Using rsync for Efficient File Collection

- Use rsync instead of zip for the primary backup mechanism
- Benefits:
  - Incremental syncing (only transfers changed files)
  - Bandwidth throttling options
  - Preservation of permissions and attributes
  - Better handling of large file sets
  - Mirror directory structure exactly

#### Collection Tool Design

- Create a modular backup collection tool that:
  - Reads source directories from config
  - Uses rsync for efficient incremental backups
  - Supports exclusion patterns (node_modules, .git, etc.)
  - Creates timestamped directories for each backup set

#### Example Configuration

```json
{
  "backup_sets": [
    {
      "name": "data",
      "sources": ["/data"],
      "method": "rsync",
      "exclusions": ["tmp/*", "*.tmp", "*.log"]
    },
    {
      "name": "config",
      "sources": ["~/.config", "~/env.sh"],
      "method": "rsync",
      "exclusions": ["~/.config/Code/Cache/*"]
    }
  ]
}
```

### Rsync Strategy for Data Directory

For the data directory, we'll use optimized rsync options:

- `rsync -av --delete` - Archive mode, verbose, and delete extraneous files
- `--block-size=131072` - Larger block size for better performance with large files
- `--exclude` patterns for unnecessary files
- `--link-dest` for hard links to unchanged files from previous backup

Example:

```bash
# For incremental backups with hardlinks to unchanged files
rsync -av --delete --block-size=131072 \
  --exclude="tmp/*" --exclude="*.log" \
  --link-dest="$DBACKUP/data-previous" \
  /data/ "$DBACKUP/data-$DATE/"

# Create symlink to latest backup
ln -sfn "data-$DATE" "$DBACKUP/data-latest"
```

Note: The `-z` compression option has been removed for local backups as it can actually slow down the process when CPU is the bottleneck rather than network bandwidth.

## External Backup Phase

### Goals

- Reliably transfer backups to external storage
- Verify backup integrity
- Handle removable media being unavailable
- Support multiple backup destinations

### Implementation Approach

#### External Transfer Tool

- Create a tool that:
  - Detects available external media (e.g., `/media/payne/T9`)
  - Syncs from $DBACKUP to external destinations
  - Verifies transfers with checksums
  - Logs successful backups
  - Handles disconnected media gracefully

#### Multiple Destination Support

- Allow configuration of multiple backup destinations
- Priority-based fallback if primary destination unavailable

#### External Drive Strategy (Optimized for T9 Performance)

The T9 external drive performs poorly with large numbers of small files but is fast with large files.
To optimize for this hardware characteristic, we'll use tar archives for external transfers:

```bash
# When transferring to external drive, create tar archives first
if [ -d "/media/payne/T9" ]; then
  # Create dated directory for this backup set
  BACKUP_DATE=$(date "+%Y-%m-%d")
  mkdir -p "/media/payne/T9/backups/$BACKUP_DATE"

  # Create single tar archive for each backup set
  tar -cf "$DBACKUP/data-latest.tar" -C "$DBACKUP" data-latest/
  tar -cf "$DBACKUP/config-latest.tar" -C "$DBACKUP" config-latest/

  # Transfer the larger, consolidated files to external drive
  rsync -av "$DBACKUP/"*".tar" "/media/payne/T9/backups/$BACKUP_DATE/"

  # Create verification file with checksums
  sha256sum "$DBACKUP/"*".tar" > "/media/payne/T9/backups/$BACKUP_DATE/verification.sha256"

  # Create a symlink to the latest backup
  ln -sfn "$BACKUP_DATE" "/media/payne/T9/backups/latest"

  # Keep only the last N backups (configurable retention)
  RETENTION=${BACKUP_RETENTION:-5}  # Default to keeping 5 backups
  ls -1d "/media/payne/T9/backups/20"* | sort -r | tail -n +$((RETENTION+1)) | xargs rm -rf
fi
```

The tar approach offers significant advantages:

- Transforms thousands of small files into a few large sequential files
- Eliminates most filesystem overhead on the external drive
- Allows for much faster transfers and verification
- Enables efficient space use with configurable retention periods

## System Integration

### Command Structure

Split the backup functionality into separate commands:

1. `backup-collect`: Gathers files into $DBACKUP

   - Runs rsync to gather specified sources
   - Creates timestamped backups
   - Rotates old backups as needed

2. `backup-external`: Transfers from $DBACKUP to external media

   - Detects external drive
   - Syncs backups to external location
   - Verifies integrity

3. `backup`: Meta-command that runs both in sequence when possible
   - Simple interface for users
   - Handles both phases when appropriate

### Scheduling and Retention

- Configurable backup schedule and retention via configuration file
- Default: full incremental backup every night, keeping last 7 local and 5 external backups
- Implemented via cron (adding to cron will be handled separately)
- Example configuration:
  ```json
  {
    "schedule": {
      "incremental": "daily", // Options: hourly, daily, weekly, monthly
      "full": "weekly", // Options: daily, weekly, monthly, never
      "external": "weekly" // Options: daily, weekly, monthly, always, manual
    },
    "retention": {
      "local": 7, // Number of local backups to retain
      "external": 5 // Number of external backups to retain
    }
  }
  ```

### Monitoring and Notifications

- Log all backup operations
- Send notifications for:
  - Successful backups
  - Failed backups
  - Missing external media
  - Low disk space warnings

## Implementation Steps

1. Create the `backup-collect` tool:

   - Implement rsync-based collection
   - Support for the identified critical directories
   - Rotation and cleanup features

2. Create the `backup-external` tool:

   - External drive detection
   - Sync mechanism with verification
   - Logging and error handling

3. Create integration components:
   - System service definitions
   - Scheduling configurations
   - Status reporting

## Restoration Tool

A dedicated restoration tool will handle recovery from backups:

### Command: `backup-restore`

1. **Functionality:**

   - List available backups (both local and external)
   - Restore specific files or entire directories
   - Verify backup integrity before restoration
   - Support both local DBACKUP and external drive sources

2. **Restoration from Local Backup:**

```bash
# Restore specific file or directory from local backup
backup-restore --source local --date 2025-04-01 --path /data/projects/important
```

3. **Restoration from External Drive:**

```bash
# List available backups on external drive
backup-restore --source external --list

# Restore from external drive (will extract from tar archives)
backup-restore --source external --date 2025-04-01 --path ~/.config
```

4. **Verification Mode:**

```bash
# Test backup validity without actually restoring
backup-restore --source external --date 2025-04-01 --verify
```

5. **Full System Restoration Guide:**
   - Include a detailed document that outlines step-by-step recovery process
   - Document critical files needed for system restoration
   - Include steps for rebuilding system from fresh install using backups

### Implementation Approach

1. For local backups:
   - Direct copying or rsync from the backup location to the target
2. For external backups:

   - Extract files from tar archives
   - Restore to original locations
   - Preserve permissions and ownership

3. For verification:
   - Check integrity of tar archives
   - Test extraction without writing to disk
   - Create report of files that would be restored

## Future Enhancements

- Encryption for sensitive backups
- Cloud backup integration (S3, Backblaze B2)
- Full-system backup image creation
- Web dashboard for backup status
- Automatic backup rotation strategies
