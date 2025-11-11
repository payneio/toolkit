---
command: android-backup
script: android/android-backup.py
description: Backup Android device using ADB
version: 1.0.0
category: android
system_dependencies:
- adb
---

# android-backup

Backup Android device data using Android Debug Bridge (ADB). Supports backing up photos, videos, documents, app data, SMS, RCS, contacts, and call logs.

## Prerequisites

- **ADB (Android Debug Bridge)** must be installed and in your PATH
- **Android device** with USB debugging enabled
- **USB connection** between computer and Android device

### Enable USB Debugging

1. Go to Settings → About Phone
2. Tap "Build Number" 7 times to enable Developer Options
3. Go to Settings → Developer Options
4. Enable "USB Debugging"
5. Connect device via USB and authorize the computer

## Installation

```bash
# Install the toolkit
cd /data/repos/toolkit
make install

# Verify installation
which android-backup

# Verify ADB is working
adb devices
```

## Usage

### Basic Usage

```bash
# Backup everything using default configuration
android-backup

# Use custom configuration file
android-backup -c custom.json

# Specify device when multiple devices connected
android-backup --device ABC123DEF456
```

### Selective Backups

```bash
# Only backup photos
android-backup --photos-only

# Only backup SMS messages
android-backup --sms-only

# Only backup contacts
android-backup --contacts-only

# Only backup call logs
android-backup --call-logs-only

# Only backup specific app data
android-backup --app-data whatsapp
android-backup --app-data com.example.app
```

### Options

```bash
android-backup [options]

Options:
  -c, --config FILE          Use custom configuration file (default: android_backup_config.json)
  --device SERIAL            Specify device serial number when multiple devices connected
  --photos-only              Only backup photos
  --videos-only              Only backup videos
  --documents-only           Only backup documents
  --sms-only                 Only backup SMS messages
  --contacts-only            Only backup contacts
  --call-logs-only           Only backup call logs
  --app-data PACKAGE         Only backup specified app data
  -v, --verbose              Enable verbose logging
  -h, --help                 Show help message
```

## Configuration

The tool uses a JSON configuration file (default: `android_backup_config.json`) to specify what to backup and where to store it.

### Example Configuration

```json
{
  "backup_root": "/data/backups/android",
  "device_name": "MyPhone",
  "backup_photos": true,
  "backup_videos": true,
  "backup_documents": true,
  "backup_sms": true,
  "backup_contacts": true,
  "backup_call_logs": true,
  "backup_app_data": ["com.whatsapp", "org.telegram.messenger"],
  "photo_dirs": ["/sdcard/DCIM", "/sdcard/Pictures"],
  "video_dirs": ["/sdcard/DCIM", "/sdcard/Movies"],
  "document_dirs": ["/sdcard/Documents", "/sdcard/Download"]
}
```

### Configuration Options

- `backup_root` - Root directory for backups
- `device_name` - Friendly name for the device
- `backup_photos` - Enable photo backup (default: true)
- `backup_videos` - Enable video backup (default: true)
- `backup_documents` - Enable document backup (default: true)
- `backup_sms` - Enable SMS backup (default: true)
- `backup_contacts` - Enable contacts backup (default: true)
- `backup_call_logs` - Enable call logs backup (default: true)
- `backup_app_data` - List of app package names to backup
- `photo_dirs` - List of directories to search for photos
- `video_dirs` - List of directories to search for videos
- `document_dirs` - List of directories to search for documents

## Backup Structure

Backups are organized by date and type:

```
/data/backups/android/MyPhone/
├── 2024-07-17_14-30-00/
│   ├── photos/
│   ├── videos/
│   ├── documents/
│   ├── sms/
│   ├── contacts/
│   ├── call_logs/
│   └── app_data/
│       ├── com.whatsapp/
│       └── org.telegram.messenger/
└── 2024-07-18_10-15-00/
    └── ...
```

## Features

- **Incremental backups** - Only copies new or changed files
- **Multiple device support** - Specify device when multiple connected
- **Selective backups** - Choose what to backup
- **App data backup** - Backup specific app data
- **Organized structure** - Date-stamped backup directories
- **Logging** - Detailed logs of backup operations

## Examples

### Full Backup

```bash
# Create full backup with default settings
android-backup
```

### Daily Automated Backup

```bash
# Set up daily backup at 2 AM using schedule tool
schedule add android-backup \
    --command "android-backup" \
    --schedule "daily" \
    --on-calendar "*-*-* 02:00:00" \
    --description "Daily Android backup"
```

### Backup Multiple Devices

```bash
# List connected devices
adb devices

# Backup specific device
android-backup --device ABC123DEF456
```

### Custom Configuration

```bash
# Create custom config
cat > my_backup_config.json <<EOF
{
  "backup_root": "/mnt/nas/android_backups",
  "device_name": "WorkPhone",
  "backup_photos": true,
  "backup_videos": false,
  "backup_app_data": ["com.slack", "com.microsoft.teams"]
}
EOF

# Use custom config
android-backup -c my_backup_config.json
```

## Troubleshooting

### Device Not Found

```bash
# Check if device is connected and authorized
adb devices

# If "unauthorized", check phone for authorization dialog
# If no devices listed, check USB connection and debugging is enabled
```

### Permission Denied

Some files may require root access. The tool will log warnings for files it cannot access but will continue with the backup.

### Multiple Devices

```bash
# List all connected devices
adb devices

# Specify which device to backup
android-backup --device SERIAL_NUMBER
```

## Notes

- Requires USB debugging to be enabled on the Android device
- Some app data may require root access
- Large backups can take significant time
- Ensure sufficient disk space for backups
- First backup will be slower; subsequent backups are incremental
