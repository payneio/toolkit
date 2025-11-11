# Android Tools

Tools for working with Android devices.

## Tools

### [android-backup](android_backup.md)

Backup Android device data using ADB. Supports photos, videos, documents, app data, SMS, RCS, contacts, and call logs.

**Quick start:**
```bash
# Enable USB debugging on your Android device
# Connect device via USB

# Full backup
android-backup

# Selective backup
android-backup --photos-only
android-backup --app-data whatsapp
```

See [android_backup.md](android_backup.md) for full documentation.
