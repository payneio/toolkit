#!/usr/bin/env python3
"""
backup-external: Transfer backups to external media

Creates tar archives of backup sets and transfers them to external media.
Optimized for drives with good performance for large files but poor performance
with many small files.

Usage: backup-external [options]

Examples:
  backup-external                  # Backup to default external location if available
  backup-external -d /media/backup # Use specific external destination
  backup-external -c custom.json   # Use custom configuration file
"""
import sys
import os
import json
import argparse
import subprocess
import datetime
import logging
import shutil

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
logger = logging.getLogger("backup-external")

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
        },
        "retention": {
            "external": 5
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

def create_tar_archive(source_dir, tar_path):
    """Create a tar archive of the source directory."""
    try:
        # Check if the source exists and is a directory or symlink to directory
        if not os.path.exists(source_dir):
            logger.warning(f"Source directory does not exist: {source_dir}")
            return False
        
        # If source_dir is a symlink, resolve it
        real_source = os.path.realpath(source_dir)
        if not os.path.isdir(real_source):
            logger.warning(f"Source is not a directory: {real_source}")
            return False
        
        # Create parent directory for tar file if needed
        os.makedirs(os.path.dirname(tar_path), exist_ok=True)
        
        # Get directory name for tar command
        source_name = os.path.basename(source_dir)
        source_parent = os.path.dirname(source_dir)
        
        # Create tar archive with exclusion for the backup tar file we're creating
        logger.info(f"Creating tar archive: {tar_path}")
        cmd = ["tar", "-cf", tar_path, 
               "--exclude=" + os.path.dirname(tar_path), # Exclude the temp directory holding our tar file 
               "-C", source_parent, source_name]
        subprocess.run(cmd, check=True)
        logger.info(f"Archive created successfully: {tar_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create tar archive: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating tar archive: {e}")
        return False

def get_free_space(path):
    """Get free space in bytes on the filesystem containing path."""
    try:
        stat = os.statvfs(path)
        # Available blocks * block size
        return stat.f_bavail * stat.f_frsize
    except Exception as e:
        logger.error(f"Error checking free space: {e}")
        return 0

def transfer_to_external(source_path, destination_dir, date_str, retention):
    """Transfer a file to external destination."""
    try:
        # Create dated directory for this backup
        backup_date_dir = os.path.join(destination_dir, date_str)
        os.makedirs(backup_date_dir, exist_ok=True)
        
        # Check if there's enough space on the destination
        source_size = os.path.getsize(source_path)
        free_space = get_free_space(destination_dir)
        
        # Add 5% buffer to required space
        required_space = source_size * 1.05  # 5% buffer
        
        if free_space < required_space:
            logger.error("Not enough space on destination drive.")
            logger.error(f"Required: {required_space/1e9:.2f} GB, Available: {free_space/1e9:.2f} GB")
            logger.error(f"Please free up at least {(required_space-free_space)/1e9:.2f} GB and try again.")
            return False
        
        # Get source file name
        source_name = os.path.basename(source_path)
        destination_path = os.path.join(backup_date_dir, source_name)
        
        # Transfer file using rsync
        logger.info(f"Transferring {source_path} to {destination_path}")
        logger.info(f"File size: {source_size/1e9:.2f} GB, Free space: {free_space/1e9:.2f} GB")
        cmd = ["rsync", "-av", source_path, destination_path]
        subprocess.run(cmd, check=True)
        
        # Try to create symlink to latest backup, but don't fail if it doesn't work
        try:
            latest_link = os.path.join(destination_dir, "latest")
            if os.path.exists(latest_link):
                if os.path.islink(latest_link):
                    os.unlink(latest_link)
                else:
                    # If it exists but is not a symlink, rename it
                    os.rename(latest_link, latest_link + ".bak")
            os.symlink(date_str, latest_link)
            logger.info(f"Created 'latest' symlink pointing to {date_str}")
        except Exception as e:
            # Log the error but continue - this is not critical
            logger.warning(f"Could not create 'latest' symlink: {e}")
            # Don't fail the backup just because of a symlink issue
            logger.warning("Continuing without creating latest symlink")
        
        # Cleanup old backups
        cleanup_external_backups(destination_dir, retention)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to transfer to external: {e}")
        return False
    except Exception as e:
        logger.error(f"Error transferring to external: {e}")
        return False

def cleanup_external_backups(destination_dir, retention):
    """Remove old backups beyond the retention period."""
    try:
        # Find all dated backup directories (format: YYYY-MM-DD)
        backup_dirs = []
        for item in os.listdir(destination_dir):
            item_path = os.path.join(destination_dir, item)
            # Skip if not a directory or is a symlink
            if not os.path.isdir(item_path) or os.path.islink(item_path):
                continue
            # Check if it matches date format
            if len(item) == 10 and item[4] == '-' and item[7] == '-':
                backup_dirs.append(item)
        
        # Sort and keep only the most recent based on retention
        backup_dirs.sort(reverse=True)
        if len(backup_dirs) > retention:
            to_delete = backup_dirs[retention:]
            for backup_dir in to_delete:
                dir_path = os.path.join(destination_dir, backup_dir)
                logger.info(f"Removing old backup: {dir_path}")
                try:
                    # Try to remove using Python's shutil
                    shutil.rmtree(dir_path)
                except PermissionError:
                    # If permission error, try using sudo rm
                    logger.warning(f"Permission error, trying alternative removal method for {dir_path}")
                    try:
                        # Try regular rm without sudo first
                        subprocess.run(["rm", "-rf", dir_path], check=False)
                    except Exception as e2:
                        logger.warning(f"Could not remove directory {dir_path}: {e2}")
                except Exception as e:
                    logger.warning(f"Could not remove directory {dir_path}: {e}")
        
        logger.info(f"Cleanup completed, kept {min(len(backup_dirs), retention)} backups")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return False
    
    return True

def create_verification_file(source_files, destination_dir, date_str):
    """Create a verification file with checksums of all archives."""
    try:
        verification_file = os.path.join(destination_dir, date_str, "verification.sha256")
        
        with open(verification_file, 'w') as f:
            for source_file in source_files:
                if os.path.exists(source_file):
                    # Calculate SHA256 checksum
                    cmd = ["sha256sum", source_file]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    checksum = result.stdout.strip()
                    
                    # Write to verification file
                    f.write(f"{checksum}\n")
        
        logger.info(f"Created verification file: {verification_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating verification file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Transfer backups to external media",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    parser.add_argument('-c', '--config', 
                        help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})")
    parser.add_argument('-b', '--backup-dir', 
                        help=f"Source backup directory (default: $DBACKUP or {DEFAULT_BACKUP_DIR})")
    parser.add_argument('-d', '--destination',
                        help="External destination directory (overrides config)")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose output")
    parser.add_argument('--version', action='version', version='backup-external 1.0.0')
    args = parser.parse_args()
    
    # Set verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load configuration
    config_path = args.config or DEFAULT_CONFIG_FILE
    config = load_config(config_path)
    
    # Determine backup directory
    backup_dir = args.backup_dir or DEFAULT_BACKUP_DIR
    if not os.path.exists(backup_dir):
        logger.error(f"Backup directory does not exist: {backup_dir}")
        return 1
    
    # Determine external destination
    destination = None
    if args.destination:
        destination = args.destination
        if not os.path.exists(destination):
            logger.error(f"Specified destination does not exist: {destination}")
            return 1
    else:
        # Look for available destination from config
        destinations = config.get("external", {}).get("destinations", [])
        destination = find_available_destination(destinations)
    
    if not destination:
        logger.error("No valid external destination found. Backup aborted.")
        return 1
    
    # Create dated directory name
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Get retention setting
    retention = config.get("retention", {}).get("external", 5)
    
    # For the new design, just copy the entire /data directory
    data_dir = "/data"
    if not os.path.exists(data_dir):
        logger.error(f"Data directory does not exist: {data_dir}")
        return 1
        
    # Create temp directory for tar file to avoid recursion
    import tempfile
    temp_dir = tempfile.mkdtemp()
    tar_file = os.path.join(temp_dir, "data-full.tar")
    success = True
    
    logger.info(f"Creating tar archive of entire data directory in temp location: {tar_file}")
    if create_tar_archive(data_dir, tar_file):
        tar_files = [tar_file]
    else:
        logger.error("Failed to create tar archive of data directory")
        success = False
        tar_files = []
    
    # Transfer tar files to external destination if any were created
    if tar_files:
        logger.info(f"Transferring {len(tar_files)} archives to external destination")
        
        # Transfer each tar file
        for tar_file in tar_files:
            if not transfer_to_external(tar_file, destination, date_str, retention):
                success = False
        
        # Create verification file
        create_verification_file(tar_files, destination, date_str)
    else:
        logger.error("No tar archives were created. External backup failed.")
        success = False
    
    # Cleanup - remove temporary directory and tar files
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Removed temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Could not remove temporary directory {temp_dir}: {e}")
    
    if success:
        logger.info("External backup completed successfully")
        return 0
    else:
        logger.error("External backup completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())