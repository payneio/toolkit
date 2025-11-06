#!/usr/bin/env python3
"""
backup-collect: Collect files from various sources into backup directory

Incrementally backs up specified directories to the central backup location
using rsync. Creates hardlinks to unchanged files from previous backups to
save disk space.

Usage: backup-collect [options]

Examples:
  backup-collect                  # Backup using default configuration
  backup-collect -c custom.json   # Use custom configuration file
  backup-collect --full           # Perform a full backup instead of incremental
"""
import sys
import os
import json
import argparse
import subprocess
import datetime
import logging

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/toolkit")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "backup-config.json")
DEFAULT_BACKUP_DIR = os.environ.get("DBACKUP", "/data/backup")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("backup-collect")

def create_default_config(config_path):
    """Create a default configuration file if none exists."""
    default_config = {
        "sources": [
            {
                "name": "config",
                "paths": [
                    os.path.expanduser("~/.config"), 
                    os.path.expanduser("~/env.sh")
                ],
                "exclusions": [
                    os.path.expanduser("~/.config/Code/Cache/*"),
                    "*/Cache/*",
                    "*/CacheStorage/*"
                ]
            }
        ],
        "retention": {
            "local": 7
        },
        "schedule": {
            "incremental": "daily",
            "full": "weekly"
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

def run_backup(source, backup_dir, date_str, incremental=True):
    """Run rsync backup for a given source configuration."""
    source_name = source["name"]
    source_paths = source["paths"]
    exclusions = source.get("exclusions", [])
    
    # Create dated and latest directory names
    dated_dir = os.path.join(backup_dir, f"{source_name}-{date_str}")
    latest_dir = os.path.join(backup_dir, f"{source_name}-latest")
    previous_dir = os.path.join(backup_dir, f"{source_name}-previous")
    
    logger.info(f"Backing up {source_name} to {dated_dir}")
    
    # Create backup directory if it doesn't exist
    os.makedirs(dated_dir, exist_ok=True)
    
    for source_path in source_paths:
        # Expand user paths like ~/.config
        expanded_path = os.path.expanduser(source_path)
        
        if not os.path.exists(expanded_path):
            logger.warning(f"Source path does not exist: {expanded_path}")
            continue
        
        # Prepare rsync command
        rsync_cmd = ["rsync", "-av", "--delete", "--block-size=131072"]
        
        # Add exclusions
        for exclusion in exclusions:
            rsync_cmd.extend(["--exclude", exclusion])
        
        # For incremental backups, use hardlinks to previous backup
        if incremental and os.path.exists(latest_dir):
            rsync_cmd.extend(["--link-dest", latest_dir])
        
        # Add source and destination with path preservation
        if os.path.isdir(expanded_path):
            # For directories, preserve the trailing slash behavior
            source_with_slash = expanded_path if expanded_path.endswith('/') else expanded_path + '/'
            rsync_cmd.extend(['-R', source_with_slash])  # -R preserves relative path
            rsync_cmd.append(dated_dir + '/')
        else:
            # For files, preserve the full path structure
            rsync_cmd.extend(['-R', expanded_path])  # -R preserves relative path
            rsync_cmd.append(dated_dir + '/')
        
        # Execute rsync
        logger.info(f"Running: {' '.join(rsync_cmd)}")
        try:
            # Use check=False to continue even if there are errors
            result = subprocess.run(rsync_cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Backup of {expanded_path} completed successfully")
            else:
                logger.error(f"Backup failed for {expanded_path}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Backup failed for {expanded_path}: {e}")
            return False
    
    # Update symlinks
    try:
        # Move previous latest to previous if it exists
        if os.path.exists(latest_dir) and os.path.islink(latest_dir):
            if os.path.exists(previous_dir):
                os.unlink(previous_dir)
            os.symlink(os.readlink(latest_dir), previous_dir)
        
        # Update latest symlink
        if os.path.exists(latest_dir):
            os.unlink(latest_dir)
        os.symlink(os.path.basename(dated_dir), latest_dir)
        logger.info(f"Updated symlinks for {source_name}")
    except Exception as e:
        logger.error(f"Failed to update symlinks: {e}")
        return False
    
    return True

def cleanup_old_backups(source, backup_dir, retention):
    """Remove old backups beyond the retention period."""
    source_name = source["name"]
    logger.info(f"Cleaning up old backups for {source_name}")
    
    try:
        # Find all dated backups for this source
        backups = sorted([
            d for d in os.listdir(backup_dir) 
            if os.path.isdir(os.path.join(backup_dir, d)) and 
            d.startswith(f"{source_name}-") and 
            not os.path.islink(os.path.join(backup_dir, d))
        ])
        
        # Keep only the most recent 'retention' number of backups
        if len(backups) > retention:
            to_delete = backups[:-retention]
            for backup in to_delete:
                backup_path = os.path.join(backup_dir, backup)
                logger.info(f"Removing old backup: {backup_path}")
                # Use subprocess to remove directories that might have read-only files
                subprocess.run(["rm", "-rf", backup_path], check=True)
        
        logger.info(f"Cleanup completed, kept {min(len(backups), retention)} backups")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Collect files from various sources into backup directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]  # Use the docstring as extended help
    )
    parser.add_argument('-c', '--config', 
                        help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})")
    parser.add_argument('-b', '--backup-dir', 
                        help=f"Backup directory (default: $DBACKUP or {DEFAULT_BACKUP_DIR})")
    parser.add_argument('-f', '--full', action='store_true',
                        help="Perform a full backup instead of incremental")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose output")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable debug output")
    parser.add_argument('--version', action='version', version='backup-collect 1.0.0')
    args = parser.parse_args()
    
    # Set verbosity
    if args.verbose or args.debug:
        logger.setLevel(logging.DEBUG)
        
    # Extra debug info
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config_path = args.config or DEFAULT_CONFIG_FILE
    config = load_config(config_path)
    
    # Determine backup directory
    backup_dir = args.backup_dir or DEFAULT_BACKUP_DIR
    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Using backup directory: {backup_dir}")
    
    # Current date for backup naming
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Determine if using incremental backup
    incremental = not args.full
    logger.info(f"Performing {'incremental' if incremental else 'full'} backup")
    
    success = True
    
    # Debug output of all config
    if args.debug:
        logger.debug(f"Using config: {json.dumps(config, indent=2)}")
        logger.debug(f"Backup dir: {backup_dir}")
        logger.debug(f"Sources to backup: {len(config.get('sources', []))}")
        for source in config.get("sources", []):
            logger.debug(f"Source: {source['name']}, Paths: {source['paths']}")
    
    # Process each source
    for source in config.get("sources", []):
        logger.info(f"Processing source: {source['name']}")
        if not run_backup(source, backup_dir, date_str, incremental):
            logger.error(f"Backup failed for {source['name']}")
            success = False
        
        # Cleanup old backups
        retention = config.get("retention", {}).get("local", 7)
        cleanup_old_backups(source, backup_dir, retention)
    
    if success:
        logger.info("All backups completed successfully")
        return 0
    else:
        logger.error("One or more backups failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())