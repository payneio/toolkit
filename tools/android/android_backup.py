#!/usr/bin/env python3
"""
android-backup: Backup Android device using ADB

Backs up Android device data using Android Debug Bridge (ADB).
Supports backing up photos, videos, documents, app data, SMS, RCS, contacts, and call logs.
Designed to work with any Android device that supports ADB.

Usage: android-backup [options]

Examples:
  android-backup                      # Backup using default configuration
  android-backup -c custom.json       # Use custom configuration file
  android-backup --photos-only        # Only backup photos
  android-backup --sms-only           # Only backup SMS messages
  android-backup --contacts-only      # Only backup contacts
  android-backup --app-data whatsapp  # Only backup WhatsApp app data
  android-backup --device serialnum   # Specify device when multiple connected
"""

import sys
import os
import json
import argparse
import subprocess
import datetime
import logging
import re
import time

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/toolkit")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "android-backup-config.json")
DEFAULT_BACKUP_DIR = os.environ.get("DBACKUP", "/data/backup")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("android-backup")


def create_default_config(config_path):
    """Create a default configuration file if none exists."""
    default_config = {
        "backup_types": [
            {
                "name": "photos",
                "enabled": True,
                "paths": ["/sdcard/DCIM", "/sdcard/Pictures"],
                "exclusions": ["*.tmp", ".*"],
            },
            {
                "name": "videos",
                "enabled": True,
                "paths": ["/sdcard/DCIM", "/sdcard/Movies", "/sdcard/Videos"],
                "exclusions": ["*.tmp", ".*"],
            },
            {
                "name": "documents",
                "enabled": True,
                "paths": ["/sdcard/Documents", "/sdcard/Download"],
                "exclusions": ["*.tmp", ".*"],
            },
            {
                "name": "app_data",
                "enabled": True,
                "apps": ["com.whatsapp", "com.signal"],
            },
            {"name": "sms", "enabled": True, "format": "json"},
            {"name": "rcs", "enabled": True, "format": "json"},
            {"name": "contacts", "enabled": True, "format": "vcf"},
            {"name": "call_logs", "enabled": True, "format": "json"},
        ],
        "retention": {"local": 5},
        "incremental": True,
        "compression_level": 9,
    }

    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(default_config, f, indent=2)

    logger.info(f"Created default configuration at {config_path}")
    return default_config


def load_config(config_path):
    """Load the configuration file or create default if it doesn't exist."""
    if not os.path.exists(config_path):
        return create_default_config(config_path)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.info("Using default configuration")
        return create_default_config(config_path + ".default")


def check_adb():
    """Check if ADB is installed and return version."""
    try:
        result = subprocess.run(
            ["adb", "version"], check=True, capture_output=True, text=True
        )
        logger.info(f"ADB detected: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB command failed: {e}")
        return False
    except FileNotFoundError:
        logger.error("ADB not found. Please install Android Debug Bridge.")
        return False


def get_connected_devices():
    """Get list of connected Android devices."""
    try:
        result = subprocess.run(
            ["adb", "devices"], check=True, capture_output=True, text=True
        )

        devices = []
        for line in result.stdout.strip().split("\n")[1:]:  # Skip the first line
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    serial = parts[0].strip()
                    status = parts[1].strip()
                    if status == "device":  # Only include authorized devices
                        devices.append(serial)

        if devices:
            logger.info(
                f"Found {len(devices)} connected device(s): {', '.join(devices)}"
            )
        else:
            logger.warning("No connected devices found")

        return devices
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get device list: {e}")
        return []


def enable_adb_backup(device=None):
    """Enable backup in developer settings and guide the user."""
    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    try:
        logger.info("Checking if USB debugging is authorized...")
        test_cmd = adb_cmd + ["shell", "echo", "Connected"]
        subprocess.run(test_cmd, check=True, capture_output=True, text=True)

        # Instead of trying to open developer settings automatically (which varies by device),
        # just guide the user through the process
        logger.info("\n=== BACKUP PREPARATION ===")
        logger.info("To prepare your device for backup, please:")
        logger.info("1. On your Android device, open Settings")
        logger.info(
            "2. Navigate to System > Developer options (or About phone > tap Build number 7 times)"
        )
        logger.info(
            "3. In Developer options, find and enable 'USB debugging' if not already enabled"
        )
        logger.info(
            "4. For app data backup, also enable 'USB debugging (Security settings)'"
        )
        logger.info("5. Accept any authorization prompts on your device")
        logger.info("6. When prompted during backup, authorize the backup operation\n")

        # Wait for user confirmation
        input("Press Enter once you've confirmed these settings on your device...")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check ADB connection: {e}")
        logger.error(
            "Please ensure your device is connected and USB debugging is authorized."
        )
        return False


def pull_files(source_path, dest_path, device=None, exclusions=None):
    """Pull files from Android device using ADB."""
    if exclusions is None:
        exclusions = []

    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)

    try:
        # First list files to check what to sync
        logger.info(f"Scanning files in {source_path}...")
        list_cmd = adb_cmd + ["shell", "find", source_path, "-type", "f"]
        result = subprocess.run(list_cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            logger.error(f"Failed to list files from {source_path}: {result.stderr}")
            return False

        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        logger.info(f"Found {len(files)} files to process")

        # Filter files based on exclusions
        filtered_files = []
        for file_path in files:
            # Skip files matching exclusion patterns
            skip = False
            for pattern in exclusions:
                if re.search(pattern.replace("*", ".*"), file_path):
                    skip = True
                    break

            if not skip:
                filtered_files.append(file_path)

        logger.info(f"Pulling {len(filtered_files)} files after applying exclusions")

        # Pull each file
        success_count = 0
        for file_path in filtered_files:
            # Get the relative path from source
            rel_path = os.path.relpath(file_path, source_path)
            target_path = os.path.join(dest_path, rel_path)

            # Create target directory
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Pull the file
            pull_cmd = adb_cmd + ["pull", file_path, target_path]
            try:
                subprocess.run(pull_cmd, check=True, capture_output=True)
                success_count += 1
                # Update progress periodically
                if success_count % 10 == 0:
                    logger.info(
                        f"Pulled {success_count}/{len(filtered_files)} files..."
                    )
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to pull {file_path}: {e}")

        logger.info(
            f"Successfully pulled {success_count}/{len(filtered_files)} files to {dest_path}"
        )
        return success_count > 0
    except Exception as e:
        logger.error(f"Error pulling files from {source_path}: {e}")
        return False


def backup_app_data(app_id, dest_path, device=None, compression_level=9):
    """Backup application data using ADB backup."""
    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)

    # Create detailed dated backup file name
    date_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    backup_file = os.path.join(dest_path, f"{app_id}_{date_str}.ab")

    try:
        logger.info(f"Starting backup for app {app_id}...")
        # Start the backup process
        backup_cmd = adb_cmd + [
            "backup",
            "-f",
            backup_file,
            "-noapk",
            f"-z{compression_level}",
            app_id,
        ]

        logger.info("Please authorize the backup on your device when prompted")
        logger.info(f"Running: {' '.join(backup_cmd)}")

        # Run backup command - this will require user interaction on the device
        process = subprocess.Popen(
            backup_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # Wait for the process to complete with periodic status updates
        while process.poll() is None:
            logger.info(
                "Backup in progress... Please confirm on your device if prompted"
            )
            time.sleep(5)

        # Check results
        _stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(f"Backup failed for {app_id}: {stderr}")
            return False

        if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
            logger.info(f"Successfully backed up {app_id} to {backup_file}")
            logger.info(
                f"Backup size: {os.path.getsize(backup_file) / 1024 / 1024:.2f} MB"
            )
            return True
        else:
            logger.error(f"Backup file is empty or not created for {app_id}")
            return False
    except Exception as e:
        logger.error(f"Error backing up app {app_id}: {e}")
        return False


def cleanup_old_backups(backup_dir, retention):
    """Remove old backups beyond the retention period."""
    # For each subdirectory in the backup dir (photos, videos, etc.)
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if not os.path.isdir(item_path):
            continue

        logger.info(f"Cleaning up old backups in {item_path}")

        try:
            # Find all dated backups (looking for YYYY-MM-DD-HH-MM-SS format)
            dated_dirs = []
            for subdir in os.listdir(item_path):
                subdir_path = os.path.join(item_path, subdir)
                if os.path.isdir(subdir_path) and re.match(
                    r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$", subdir
                ):
                    dated_dirs.append(subdir)

            # Sort by date (newest first)
            dated_dirs.sort(reverse=True)

            # Keep only the most recent 'retention' backups
            if len(dated_dirs) > retention:
                for old_dir in dated_dirs[retention:]:
                    dir_to_remove = os.path.join(item_path, old_dir)
                    logger.info(f"Removing old backup: {dir_to_remove}")
                    subprocess.run(["rm", "-rf", dir_to_remove], check=True)

            logger.info(
                f"Cleanup completed in {item_path}, kept {min(len(dated_dirs), retention)} backups"
            )
        except Exception as e:
            logger.error(f"Error during cleanup in {item_path}: {e}")


def backup_sms(dest_path, device=None, format="json"):
    """Backup SMS messages from the device."""
    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)

    # Get current date for filename
    date_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    sms_file = os.path.join(dest_path, f"sms_{date_str}.{format}")

    logger.info(f"Backing up SMS messages to {sms_file}...")

    try:
        # Query SMS database using content provider
        cmd = adb_cmd + [
            "shell",
            "content query --uri content://sms --projection _id,address,date,body,type,read",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Process the output
        sms_list = []
        current_sms = {}

        for line in result.stdout.splitlines():
            if not line.strip():
                if current_sms:
                    sms_list.append(current_sms)
                    current_sms = {}
                continue

            # Parse each line of output (format: "column=value")
            for item in line.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    current_sms[key] = value

        # Add the last SMS
        if current_sms:
            sms_list.append(current_sms)

        # Save to file in the requested format
        if format.lower() == "json":
            with open(sms_file, "w") as f:
                json.dump(sms_list, f, indent=2)
        elif format.lower() == "csv":
            import csv

            with open(sms_file, "w", newline="") as f:
                if sms_list:
                    writer = csv.DictWriter(f, fieldnames=sms_list[0].keys())
                    writer.writeheader()
                    writer.writerows(sms_list)

        logger.info(f"Successfully backed up {len(sms_list)} SMS messages")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to backup SMS: {e}")
        logger.error(f"Output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error backing up SMS: {e}")
        return False


def backup_rcs(dest_path, device=None, format="json"):
    """Backup RCS messages from the device."""
    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)

    # Get current date for filename
    date_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    rcs_file = os.path.join(dest_path, f"rcs_{date_str}.{format}")

    logger.info(f"Backing up RCS messages to {rcs_file}...")

    try:
        # Query RCS database using content provider (if available)
        # Note: RCS provider URI may vary by Android version and messaging app
        cmd = adb_cmd + [
            "shell",
            "content query --uri content://mms-sms/conversations --projection thread_id,recipient_ids,date,snippet",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # If the standard approach doesn't work, try to backup via Google Messages app data
        if "Error" in result.stderr or not result.stdout.strip():
            logger.warning(
                "Standard RCS query failed, attempting to backup via Google Messages app data"
            )
            messages_backup = backup_app_data(
                "com.google.android.apps.messaging",
                dest_path,
                device,
                compression_level=9,
            )

            if messages_backup:
                logger.info("Backed up RCS via Google Messages app data")
                return True
            else:
                logger.error("Failed to backup RCS messages")
                return False

        # Process the output
        rcs_list = []
        current_rcs = {}

        for line in result.stdout.splitlines():
            if not line.strip():
                if current_rcs:
                    rcs_list.append(current_rcs)
                    current_rcs = {}
                continue

            # Parse each line of output
            for item in line.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    current_rcs[key] = value

        # Add the last entry
        if current_rcs:
            rcs_list.append(current_rcs)

        # Save to file in the requested format
        if format.lower() == "json":
            with open(rcs_file, "w") as f:
                json.dump(rcs_list, f, indent=2)
        elif format.lower() == "csv":
            import csv

            with open(rcs_file, "w", newline="") as f:
                if rcs_list:
                    writer = csv.DictWriter(f, fieldnames=rcs_list[0].keys())
                    writer.writeheader()
                    writer.writerows(rcs_list)

        logger.info(f"Successfully backed up {len(rcs_list)} RCS conversation threads")
        return True
    except Exception as e:
        logger.error(f"Error backing up RCS: {e}")
        return False


def backup_contacts(dest_path, device=None, format="vcf"):
    """Backup contacts from the device."""
    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)

    # Get current date for filename
    date_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    contacts_file = os.path.join(dest_path, f"contacts_{date_str}.{format}")

    logger.info(f"Backing up contacts to {contacts_file}...")

    try:
        if format.lower() == "vcf":
            # Export contacts to VCF using built-in Android export command
            export_cmd = adb_cmd + [
                "shell",
                "am start -a android.intent.action.MAIN -n com.android.contacts/.activities.PeopleActivity",
            ]
            subprocess.run(export_cmd, capture_output=True, check=False)

            # Wait a moment for the contacts app to open
            time.sleep(2)

            # Try direct content provider query for modern Android versions
            query_cmd = adb_cmd + [
                "shell",
                "content query --uri content://com.android.contacts/data --projection raw_contact_id,display_name,data1,data2,data3",
            ]
            query_result = subprocess.run(
                query_cmd, capture_output=True, text=True, check=False
            )

            if query_result.returncode == 0 and query_result.stdout.strip():
                # Process content provider results
                contacts_data = query_result.stdout

                # Parse the data and create VCF format
                vcf_content = "BEGIN:VCARD\nVERSION:3.0\n"

                current_contact = {}
                for line in contacts_data.splitlines():
                    if not line.strip():
                        if current_contact:
                            # Add contact to VCF
                            if "display_name" in current_contact:
                                vcf_content += f"FN:{current_contact['display_name']}\n"
                            if (
                                "data1" in current_contact
                                and "data2" in current_contact
                                and current_contact.get("data2") == "1"
                            ):
                                # Phone number
                                vcf_content += f"TEL:{current_contact['data1']}\n"
                            if (
                                "data1" in current_contact
                                and "data2" in current_contact
                                and current_contact.get("data2") == "2"
                            ):
                                # Email
                                vcf_content += f"EMAIL:{current_contact['data1']}\n"

                            vcf_content += "END:VCARD\nBEGIN:VCARD\nVERSION:3.0\n"
                            current_contact = {}
                        continue

                    # Parse line
                    for item in line.split(","):
                        if "=" in item:
                            key, value = item.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            current_contact[key] = value

                # Close the last contact
                if current_contact:
                    if "display_name" in current_contact:
                        vcf_content += f"FN:{current_contact['display_name']}\n"
                    if (
                        "data1" in current_contact
                        and "data2" in current_contact
                        and current_contact.get("data2") == "1"
                    ):
                        vcf_content += f"TEL:{current_contact['data1']}\n"
                    if (
                        "data1" in current_contact
                        and "data2" in current_contact
                        and current_contact.get("data2") == "2"
                    ):
                        vcf_content += f"EMAIL:{current_contact['data1']}\n"
                    vcf_content += "END:VCARD\n"

                # Write VCF file
                with open(contacts_file, "w") as f:
                    f.write(vcf_content)

                logger.info(f"Successfully backed up contacts to {contacts_file}")
                return True
            else:
                # Fall back to app data backup
                logger.warning(
                    "Direct contacts query failed, attempting to backup via Contacts app data"
                )
                contacts_backup = backup_app_data(
                    "com.android.contacts", dest_path, device, compression_level=9
                )

                if contacts_backup:
                    logger.info("Backed up contacts via Contacts app data")
                    return True
                else:
                    logger.error("Failed to backup contacts")
                    return False
        else:
            # For other formats, query the contacts database
            cmd = adb_cmd + [
                "shell",
                "content query --uri content://contacts/phones --projection display_name,number,type",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Process the output
            contacts_list = []
            current_contact = {}

            for line in result.stdout.splitlines():
                if not line.strip():
                    if current_contact:
                        contacts_list.append(current_contact)
                        current_contact = {}
                    continue

                # Parse each line of output
                for item in line.split(","):
                    if "=" in item:
                        key, value = item.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        current_contact[key] = value

            # Add the last contact
            if current_contact:
                contacts_list.append(current_contact)

            # Save to file in the requested format
            if format.lower() == "json":
                with open(contacts_file, "w") as f:
                    json.dump(contacts_list, f, indent=2)
            elif format.lower() == "csv":
                import csv

                with open(contacts_file, "w", newline="") as f:
                    if contacts_list:
                        writer = csv.DictWriter(f, fieldnames=contacts_list[0].keys())
                        writer.writeheader()
                        writer.writerows(contacts_list)

            logger.info(f"Successfully backed up {len(contacts_list)} contacts")
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to backup contacts: {e}")
        return False
    except Exception as e:
        logger.error(f"Error backing up contacts: {e}")
        return False


def backup_call_logs(dest_path, device=None, format="json"):
    """Backup call logs from the device."""
    adb_cmd = ["adb"]
    if device:
        adb_cmd.extend(["-s", device])

    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)

    # Get current date for filename
    date_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    call_log_file = os.path.join(dest_path, f"call_logs_{date_str}.{format}")

    logger.info(f"Backing up call logs to {call_log_file}...")

    try:
        # Query call logs using content provider
        cmd = adb_cmd + [
            "shell",
            "content query --uri content://call_log/calls --projection number,type,date,duration,name",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Process the output
        call_list = []
        current_call = {}

        for line in result.stdout.splitlines():
            if not line.strip():
                if current_call:
                    call_list.append(current_call)
                    current_call = {}
                continue

            # Parse each line of output
            for item in line.split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    current_call[key] = value

        # Add the last call
        if current_call:
            call_list.append(current_call)

        # Save to file in the requested format
        if format.lower() == "json":
            with open(call_log_file, "w") as f:
                json.dump(call_list, f, indent=2)
        elif format.lower() == "csv":
            import csv

            with open(call_log_file, "w", newline="") as f:
                if call_list:
                    writer = csv.DictWriter(f, fieldnames=call_list[0].keys())
                    writer.writeheader()
                    writer.writerows(call_list)

        logger.info(f"Successfully backed up {len(call_list)} call log entries")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to backup call logs: {e}")
        return False
    except Exception as e:
        logger.error(f"Error backing up call logs: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Backup Android device using ADB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]
        if __doc__
        else "",  # Use the docstring as extended help
    )
    parser.add_argument(
        "-c", "--config", help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})"
    )
    parser.add_argument(
        "-b",
        "--backup-dir",
        help=f"Backup directory (default: $DBACKUP/android or {DEFAULT_BACKUP_DIR}/android)",
    )
    parser.add_argument(
        "-d",
        "--device",
        help="Specific device serial number (for multiple connected devices)",
    )
    parser.add_argument("--photos-only", action="store_true", help="Only backup photos")
    parser.add_argument("--videos-only", action="store_true", help="Only backup videos")
    parser.add_argument(
        "--documents-only", action="store_true", help="Only backup documents"
    )
    parser.add_argument(
        "--sms-only", action="store_true", help="Only backup SMS messages"
    )
    parser.add_argument(
        "--rcs-only", action="store_true", help="Only backup RCS messages"
    )
    parser.add_argument(
        "--contacts-only", action="store_true", help="Only backup contacts"
    )
    parser.add_argument(
        "--call-logs-only", action="store_true", help="Only backup call logs"
    )
    parser.add_argument(
        "--app-data", help="Only backup specific app data (e.g., 'com.whatsapp')"
    )
    parser.add_argument(
        "--list-devices", action="store_true", help="List connected devices and exit"
    )
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="Perform a full backup instead of incremental",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("--version", action="version", version="android-backup 1.0.0")
    args = parser.parse_args()

    # Set verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Check if ADB is installed
    if not check_adb():
        logger.error(
            "ADB is required but not found. Please install Android Debug Bridge."
        )
        return 1

    # List devices and exit if requested
    if args.list_devices:
        devices = get_connected_devices()
        if devices:
            print("Connected Android devices:")
            for i, device in enumerate(devices, 1):
                print(f"{i}. {device}")
            return 0
        else:
            print("No Android devices connected.")
            return 1

    # Get connected devices
    devices = get_connected_devices()
    if not devices:
        logger.error(
            "No Android devices connected. Please connect a device and try again."
        )
        return 1

    # Select device
    device = None
    if args.device:
        if args.device in devices:
            device = args.device
        else:
            logger.error(
                f"Specified device {args.device} not found in connected devices."
            )
            return 1
    elif len(devices) > 1:
        logger.warning(
            "Multiple devices connected. Please specify a device with --device."
        )
        print("Connected devices:")
        for i, dev in enumerate(devices, 1):
            print(f"{i}. {dev}")
        return 1
    else:
        device = devices[0]

    # Enable ADB backup on the device
    if not enable_adb_backup(device):
        return 1

    # Load configuration
    config_path = args.config or DEFAULT_CONFIG_FILE
    config = load_config(config_path)

    # Determine backup directory
    backup_base_dir = args.backup_dir or os.path.join(DEFAULT_BACKUP_DIR, "android")
    os.makedirs(backup_base_dir, exist_ok=True)
    logger.info(f"Using backup directory: {backup_base_dir}")

    # Create detailed dated subdirectory for this backup
    date_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Determine backup types to run based on command-line arguments
    types_to_backup = []
    if args.photos_only:
        types_to_backup = ["photos"]
    elif args.videos_only:
        types_to_backup = ["videos"]
    elif args.documents_only:
        types_to_backup = ["documents"]
    elif args.sms_only:
        types_to_backup = ["sms"]
    elif args.rcs_only:
        types_to_backup = ["rcs"]
    elif args.contacts_only:
        types_to_backup = ["contacts"]
    elif args.call_logs_only:
        types_to_backup = ["call_logs"]
    elif args.app_data:
        types_to_backup = ["app_data"]
        # Override app list with the specific app
        for btype in config["backup_types"]:
            if btype["name"] == "app_data":
                btype["apps"] = [args.app_data]
    else:
        # Use all enabled types from config
        types_to_backup = [
            btype["name"]
            for btype in config["backup_types"]
            if btype.get("enabled", True)
        ]

    logger.info(f"Will backup the following types: {', '.join(types_to_backup)}")

    # Determine incremental backup
    incremental = config.get("incremental", True) and not args.full
    logger.info(f"Performing {'incremental' if incremental else 'full'} backup")

    # Process each backup type
    success = True
    for backup_type in config["backup_types"]:
        if backup_type["name"] not in types_to_backup:
            continue

        logger.info(f"Processing backup type: {backup_type['name']}")

        if backup_type["name"] == "app_data":
            # App data backup
            app_dir = os.path.join(backup_base_dir, "app_data")
            os.makedirs(app_dir, exist_ok=True)

            for app_id in backup_type["apps"]:
                app_backup_dir = os.path.join(app_dir, app_id)
                os.makedirs(app_backup_dir, exist_ok=True)

                if not backup_app_data(
                    app_id, app_backup_dir, device, config.get("compression_level", 9)
                ):
                    logger.error(f"Backup failed for app {app_id}")
                    success = False
        elif backup_type["name"] == "sms":
            # SMS backup
            sms_dir = os.path.join(backup_base_dir, "sms")
            os.makedirs(sms_dir, exist_ok=True)

            if not backup_sms(sms_dir, device, backup_type.get("format", "json")):
                logger.error("SMS backup failed")
                success = False
        elif backup_type["name"] == "rcs":
            # RCS backup
            rcs_dir = os.path.join(backup_base_dir, "rcs")
            os.makedirs(rcs_dir, exist_ok=True)

            if not backup_rcs(rcs_dir, device, backup_type.get("format", "json")):
                logger.error("RCS backup failed")
                success = False
        elif backup_type["name"] == "contacts":
            # Contacts backup
            contacts_dir = os.path.join(backup_base_dir, "contacts")
            os.makedirs(contacts_dir, exist_ok=True)

            if not backup_contacts(
                contacts_dir, device, backup_type.get("format", "vcf")
            ):
                logger.error("Contacts backup failed")
                success = False
        elif backup_type["name"] == "call_logs":
            # Call logs backup
            call_logs_dir = os.path.join(backup_base_dir, "call_logs")
            os.makedirs(call_logs_dir, exist_ok=True)

            if not backup_call_logs(
                call_logs_dir, device, backup_type.get("format", "json")
            ):
                logger.error("Call logs backup failed")
                success = False
        else:
            # File-based backup
            backup_paths = backup_type.get("paths", [])
            exclusions = backup_type.get("exclusions", [])

            # Determine file type extensions for filtering
            file_extensions = []
            if backup_type["name"] == "photos":
                file_extensions = [".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif"]
            elif backup_type["name"] == "videos":
                file_extensions = [".mp4", ".mov", ".3gp", ".mkv", ".webm", ".avi"]
            elif backup_type["name"] == "documents":
                file_extensions = [
                    ".pdf",
                    ".doc",
                    ".docx",
                    ".xls",
                    ".xlsx",
                    ".ppt",
                    ".pptx",
                    ".txt",
                ]

            # Create type-specific backup directory with date
            type_backup_dir = os.path.join(
                backup_base_dir, backup_type["name"], date_str
            )

            # Setup adb command with device if specified.
            adb_cmd = ["adb"]
            if device:
                adb_cmd.extend(["-s", device])

            for source_path in backup_paths:
                # Verify source path exists
                check_cmd = adb_cmd + ["shell", "[ -d", source_path, "] && echo exists"]
                check_result = subprocess.run(
                    check_cmd, capture_output=True, text=True, check=False
                )

                if "exists" not in check_result.stdout:
                    logger.warning(
                        f"Source path {source_path} does not exist, skipping"
                    )
                    continue

                # For media files, use a more direct approach with specific file types
                if file_extensions:
                    logger.info(
                        f"Backing up {backup_type['name']} from {source_path}..."
                    )

                    # Create destination directory
                    os.makedirs(type_backup_dir, exist_ok=True)

                    # For each extension, find and pull matching files
                    for ext in file_extensions:
                        # Find command with wildcard extension
                        find_cmd = adb_cmd + [
                            "shell",
                            f"find {source_path} -type f -iname '*{ext}'",
                        ]
                        find_result = subprocess.run(
                            find_cmd, capture_output=True, text=True, check=False
                        )

                        if find_result.returncode == 0 and find_result.stdout.strip():
                            files = [
                                f.strip()
                                for f in find_result.stdout.splitlines()
                                if f.strip()
                            ]
                            logger.info(
                                f"Found {len(files)} {ext} files in {source_path}"
                            )

                            # Pull each file
                            for file_path in files:
                                # Get the relative path from source
                                rel_path = os.path.relpath(file_path, source_path)
                                target_path = os.path.join(type_backup_dir, rel_path)

                                # Create target directory
                                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                                # Pull the file
                                pull_cmd = adb_cmd + ["pull", file_path, target_path]
                                try:
                                    subprocess.run(
                                        pull_cmd, check=True, capture_output=True
                                    )
                                    logger.info(f"Pulled {file_path}")
                                except subprocess.CalledProcessError as e:
                                    logger.warning(f"Failed to pull {file_path}: {e}")
                else:
                    # For other types, use the original exclusion approach
                    path_exclusions = list(exclusions)  # Make a copy

                    # Add -type f to only find files
                    if not pull_files(
                        source_path, type_backup_dir, device, path_exclusions
                    ):
                        logger.warning(f"Backup may be incomplete for {source_path}")
                        # Don't fail completely for file backups, just log the warning

    # Cleanup old backups
    retention = config.get("retention", {}).get("local", 5)
    cleanup_old_backups(backup_base_dir, retention)

    if success:
        logger.info("Android backup completed successfully")
        return 0
    else:
        logger.error("Android backup completed with errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
