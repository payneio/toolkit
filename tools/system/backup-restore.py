#!/usr/bin/env python3
"""
backup-restore: Restore files from backup

Restores files from local or external backups. Can list available backups,
restore specific files or directories, and verify backup integrity.

Usage: backup-restore [options]

Examples:
  backup-restore --list                   # List available backups
  backup-restore --source local --list    # List available local backups
  backup-restore --source external --list # List available external backups
  
  # Restore a specific file or directory from local backup
  backup-restore --source local --date 2025-04-01 --path /data/projects/important

  # Restore a specific file or directory from external backup
  backup-restore --source external --date 2025-04-01 --path ~/.config

  # Verify backup integrity without restoring
  backup-restore --source external --date 2025-04-01 --verify
"""
import sys
import os
import json
import argparse
import subprocess
import datetime
import logging
import glob
import tempfile
from pathlib import Path

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/toolkit")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "backup-config.json")
DEFAULT_BACKUP_DIR = os.environ.get("DBACKUP", "/data/backup")
DEFAULT_EXTERNAL_LOCATIONS = [
    "/media/payne/T9/backups",
    "/mnt/backup",
    "/media/backup"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("backup-restore")

def create_default_config(config_path):
    """Create a default configuration file if none exists."""
    default_config = {
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
        }
    }
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    logger.info(f"Created default configuration at {config_path}")
    return default_config

def load_config(config_path):
    """Load the configuration file or create default if it doesn't exist."""
    if not os.path.exists(config_path):
        return create_default_config(config_path)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.info("Using default configuration")
        return create_default_config(config_path + ".default")

def find_available_destination(destinations):
    """Find the highest priority available destination."""
    # Sort destinations by priority (lowest number is highest priority)
    sorted_destinations = sorted(destinations, key=lambda x: x.get("priority", 999))
    
    for destination in sorted_destinations:
        path = destination.get("path")
        if path and os.path.exists(path) and os.path.isdir(path):
            logger.info(f"Found available destination: {path}")
            return path
    
    logger.warning("No available external destinations found")
    return None

def list_local_backups(backup_dir):
    """List all available local backups."""
    backup_sets = {}
    
    # Find all backup sets with "-latest" symlinks
    latest_symlinks = glob.glob(os.path.join(backup_dir, "*-latest"))
    
    for symlink in latest_symlinks:
        set_name = os.path.basename(symlink).replace("-latest", "")
        backup_sets[set_name] = []
        
        # Find all dated backups for this set
        backup_pattern = os.path.join(backup_dir, f"{set_name}-*")
        backup_dirs = glob.glob(backup_pattern)
        
        for backup_dir in backup_dirs:
            # Skip symlinks
            if os.path.islink(backup_dir):
                continue
            
            # Extract date from directory name
            dir_name = os.path.basename(backup_dir)
            if dir_name.startswith(f"{set_name}-"):
                date_str = dir_name[len(set_name)+1:]
                backup_sets[set_name].append(date_str)
    
    # Sort dates from newest to oldest
    for set_name in backup_sets:
        backup_sets[set_name].sort(reverse=True)
    
    return backup_sets

def list_external_backups(destination_dir):
    """List all available external backups."""
    if not os.path.exists(destination_dir):
        logger.error(f"External destination directory does not exist: {destination_dir}")
        return {}
    
    backup_dates = []
    
    # List all dated directories (YYYY-MM-DD format)
    for item in os.listdir(destination_dir):
        item_path = os.path.join(destination_dir, item)
        if os.path.isdir(item_path) and not os.path.islink(item_path):
            # Check if it matches date format
            if len(item) == 10 and item[4] == '-' and item[7] == '-':
                backup_dates.append(item)
    
    # Sort dates from newest to oldest
    backup_dates.sort(reverse=True)
    
    # Get backup sets from latest backup
    backup_sets = {}
    if backup_dates:
        latest_dir = os.path.join(destination_dir, backup_dates[0])
        for item in os.listdir(latest_dir):
            if item.endswith(".tar"):
                set_name = item.replace("-latest.tar", "")
                backup_sets[set_name] = backup_dates
    
    return backup_sets

def print_backup_list(backup_sets, source_type):
    """Print the list of available backups in a formatted way."""
    if not backup_sets:
        print(f"No {source_type} backups found.")
        return
    
    print(f"\nAvailable {source_type} backups:")
    print("=" * 60)
    
    for set_name in sorted(backup_sets.keys()):
        print(f"\n{set_name}:")
        for date_str in backup_sets[set_name][:5]:  # Show only 5 most recent
            print(f"  - {date_str}")
        
        if len(backup_sets[set_name]) > 5:
            print(f"  ... and {len(backup_sets[set_name])-5} more")
    
    print("\nTo restore, use: backup-restore --source", source_type, "--date DATE --path PATH")

def restore_from_local(backup_dir, set_name, date_str, restore_path, target_path):
    """Restore files from a local backup."""
    # Find the backup directory
    source_dir = os.path.join(backup_dir, f"{set_name}-{date_str}")
    
    if not os.path.exists(source_dir):
        logger.error(f"Backup not found: {source_dir}")
        return False
    
    # Construct source path within the backup
    source_path = os.path.join(source_dir, restore_path.lstrip('/'))
    
    if not os.path.exists(source_path):
        logger.error(f"Path not found in backup: {source_path}")
        return False
    
    # Create target directory if needed
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    # Use rsync to restore the files
    logger.info(f"Restoring {source_path} to {target_path}")
    cmd = ["rsync", "-av", source_path, target_path]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Restore completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Restore failed: {e}")
        return False

def extract_from_tar(tar_file, restore_path, target_path, dry_run=False):
    """Extract files from a tar archive."""
    try:
        # Create temp directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract only the needed path from the tar
            extract_path = restore_path.lstrip('/')
            
            # First list the contents to see if the path exists
            cmd = ["tar", "-tf", tar_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Check if the path exists in the archive
            found = False
            for line in result.stdout.splitlines():
                if line.startswith(extract_path):
                    found = True
                    break
            
            if not found:
                logger.error(f"Path not found in tar archive: {extract_path}")
                return False
            
            if dry_run:
                logger.info(f"Verification: Path exists in tar archive: {extract_path}")
                return True
            
            # Extract to temp directory
            logger.info(f"Extracting {extract_path} from {tar_file}")
            extract_cmd = ["tar", "-xf", tar_file, "-C", temp_dir, extract_path]
            subprocess.run(extract_cmd, check=True)
            
            # Move to target location
            extracted_path = os.path.join(temp_dir, extract_path)
            if not os.path.exists(extracted_path):
                logger.error(f"Extraction failed, path not found: {extracted_path}")
                return False
            
            # Create target directory if needed
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Use rsync to preserve permissions
            cmd = ["rsync", "-av", extracted_path, target_path]
            subprocess.run(cmd, check=True)
            
            logger.info(f"Restored {extract_path} to {target_path}")
            return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Extraction failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        return False

def restore_from_external(destination_dir, set_name, date_str, restore_path, target_path, verify_only=False):
    """Restore files from an external backup."""
    # Find the tar archive
    backup_date_dir = os.path.join(destination_dir, date_str)
    
    # If set_name is "data", look for data-full.tar
    if set_name == "data":
        tar_file = os.path.join(backup_date_dir, "data-full.tar")
    else:
        tar_file = os.path.join(backup_date_dir, f"{set_name}-latest.tar")
    
    if not os.path.exists(tar_file):
        logger.error(f"Backup archive not found: {tar_file}")
        return False
    
    # Extract from tar
    return extract_from_tar(tar_file, restore_path, target_path, dry_run=verify_only)

def verify_checksum(destination_dir, date_str):
    """Verify checksums of backup archives."""
    backup_date_dir = os.path.join(destination_dir, date_str)
    verification_file = os.path.join(backup_date_dir, "verification.sha256")
    
    if not os.path.exists(verification_file):
        logger.error(f"Verification file not found: {verification_file}")
        return False
    
    try:
        # Change to the backup directory to verify
        original_dir = os.getcwd()
        os.chdir(backup_date_dir)
        
        # Run sha256sum check
        cmd = ["sha256sum", "-c", "verification.sha256"]
        subprocess.run(cmd, check=True)
        
        # Change back to original directory
        os.chdir(original_dir)
        
        logger.info(f"Checksum verification passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Checksum verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Restore files from backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    parser.add_argument('-c', '--config', 
                        help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})")
    parser.add_argument('-b', '--backup-dir', 
                        help=f"Local backup directory (default: $DBACKUP or {DEFAULT_BACKUP_DIR})")
    parser.add_argument('-d', '--destination',
                        help="External destination directory (overrides config)")
    parser.add_argument('-s', '--source', choices=['local', 'external'], default='local',
                        help="Source of backup to restore (local or external)")
    parser.add_argument('--list', action='store_true',
                        help="List available backups")
    parser.add_argument('--date', 
                        help="Date of backup to restore (YYYY-MM-DD for external, timestamp for local)")
    parser.add_argument('--set',
                        help="Backup set to restore (e.g., 'data', 'config')")
    parser.add_argument('--path',
                        help="Path within backup to restore")
    parser.add_argument('--target',
                        help="Target location for restored files (default: original location)")
    parser.add_argument('--verify', action='store_true',
                        help="Verify backup integrity without restoring")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose output")
    parser.add_argument('--version', action='version', version='backup-restore 1.0.0')
    args = parser.parse_args()
    
    # Set verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load configuration
    config_path = args.config or DEFAULT_CONFIG_FILE
    config = load_config(config_path)
    
    # Determine backup directories
    backup_dir = args.backup_dir or DEFAULT_BACKUP_DIR
    
    # Determine external destination
    destination = None
    if args.source == 'external':
        if args.destination:
            destination = args.destination
        else:
            # Look for available destination from config
            destinations = config.get("external", {}).get("destinations", [])
            destination = find_available_destination(destinations)
        
        if not destination:
            logger.error("No valid external destination found.")
            return 1
    
    # List available backups
    if args.list:
        if args.source == 'local':
            backup_sets = list_local_backups(backup_dir)
            print_backup_list(backup_sets, "local")
        else:  # external
            backup_sets = list_external_backups(destination)
            print_backup_list(backup_sets, "external")
        return 0
    
    # Verify backup integrity
    if args.verify:
        if not args.date:
            logger.error("Date must be specified for verification")
            return 1
        
        if args.source == 'external':
            # For external, verify checksums
            if verify_checksum(destination, args.date):
                logger.info("Backup verification successful")
                # If path specified, also verify the specific path
                if args.path and args.set:
                    backup_date_dir = os.path.join(destination, args.date)
                    tar_file = os.path.join(backup_date_dir, f"{args.set}-latest.tar")
                    if restore_from_external(destination, args.set, args.date, args.path, args.path, verify_only=True):
                        logger.info(f"Path verification successful: {args.path}")
                    else:
                        logger.error(f"Path verification failed: {args.path}")
                        return 1
                return 0
            else:
                logger.error("Backup verification failed")
                return 1
        else:
            # For local, just check if backup exists
            if not args.set:
                logger.error("Backup set must be specified for verification")
                return 1
            
            source_dir = os.path.join(backup_dir, f"{args.set}-{args.date}")
            if os.path.exists(source_dir):
                logger.info(f"Backup exists: {source_dir}")
                
                # If path specified, verify the specific path
                if args.path:
                    source_path = os.path.join(source_dir, args.path.lstrip('/'))
                    if os.path.exists(source_path):
                        logger.info(f"Path verification successful: {args.path}")
                        return 0
                    else:
                        logger.error(f"Path not found in backup: {args.path}")
                        return 1
                return 0
            else:
                logger.error(f"Backup not found: {source_dir}")
                return 1
    
    # Restore files
    if not args.date or not args.path:
        logger.error("Both date and path must be specified for restoration")
        parser.print_help()
        return 1
    
    if not args.set:
        logger.error("Backup set must be specified for restoration")
        parser.print_help()
        return 1
    
    # Determine target path (default to original location)
    target_path = args.target or args.path
    
    # Expand user paths
    restore_path = os.path.expanduser(args.path)
    target_path = os.path.expanduser(target_path)
    
    # Perform restoration
    if args.source == 'local':
        success = restore_from_local(backup_dir, args.set, args.date, restore_path, target_path)
    else:  # external
        success = restore_from_external(destination, args.set, args.date, restore_path, target_path)
    
    if success:
        logger.info(f"Restoration completed successfully to {target_path}")
        return 0
    else:
        logger.error("Restoration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())