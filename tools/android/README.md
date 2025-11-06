# Android Tools

A collection of tools for interacting with Android devices.

## Tools

### android-backup

A comprehensive backup tool for Android devices using ADB.

**Features:**
- Back up photos, videos, and documents from device storage
- Back up SMS messages and call logs
- Back up contacts (VCF, JSON, or CSV format)
- Back up RCS messages
- Back up app data for specific applications
- Incremental and full backup options
- Configurable retention policies
- Support for multiple connected devices

**Prerequisites:**
- Android Debug Bridge (ADB) installed on your system
- USB debugging enabled on your Android device
- Device authorized for USB debugging on your computer

**Usage:**

```bash
# Run a full backup with default settings
android-backup

# Only backup photos
android-backup --photos-only

# Only backup contacts
android-backup --contacts-only

# Only backup SMS messages
android-backup --sms-only

# Only backup specific app data (e.g., WhatsApp)
android-backup --app-data com.whatsapp

# List connected devices
android-backup --list-devices

# Specify a particular device when multiple are connected
android-backup --device DEVICE_SERIAL_NUMBER

# Use custom configuration file
android-backup --config /path/to/config.json

# Use custom backup directory
android-backup --backup-dir /path/to/backup/dir

# Perform a full backup (non-incremental)
android-backup --full
```

**Configuration:**

The tool uses a JSON configuration file located at `~/.config/toolkit/android-backup-config.json`. You can customize:
- What types of data to backup
- File paths for media files
- File exclusion patterns
- Backup retention periods
- Compression settings

## Adding New Tools

To add a new Android tool to this directory:

1. Create a Python script in this directory
2. Add an entry to `tools.toml`
3. Update this README with documentation
4. Make sure to add any required system dependencies