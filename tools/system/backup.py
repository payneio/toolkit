#!/usr/bin/env python3
"""
backup: Complete backup system (both local and external phases)

Performs a complete backup operation, first collecting files from
various sources into the backup directory, then transferring them
to external media if available.

Usage: backup [options]

Examples:
  backup                 # Run both backup phases
  backup --local-only    # Only run the local backup phase
  backup --external-only # Only run the external backup phase
  backup --full          # Perform a full backup instead of incremental
"""

import sys
import os
import json
import argparse
import subprocess
import logging

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/toolkit")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "backup-config.json")
DEFAULT_BACKUP_DIR = os.environ.get("DBACKUP", "/data/backup")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backup")


def create_default_config(config_path):
    """Create a default configuration file if none exists."""
    default_config = {
        "sources": [
            {
                "name": "config",
                "paths": [
                    os.path.expanduser("~/.config"),
                    os.path.expanduser("~/env.sh"),
                    os.path.expanduser("~/.secrets"),
                ],
                "exclusions": [
                    os.path.expanduser("~/.config/Code/Cache/*"),
                    "*/Cache/*",
                    "*/CacheStorage/*",
                ],
            }
        ],
        "external": {
            "destinations": [
                {"name": "t9_drive", "path": "/media/payne/T9/backups", "priority": 1},
                {"name": "backup_mount", "path": "/mnt/backup", "priority": 2},
            ]
        },
        "retention": {"local": 7, "external": 5},
        "schedule": {"incremental": "daily", "full": "weekly", "external": "weekly"},
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


def run_backup_collect(args):
    """Run the backup-collect tool with the given arguments."""
    logger.info("Starting local backup collection phase...")

    cmd = ["backup-collect"]

    # Pass through relevant arguments
    if args.config:
        cmd.extend(["-c", args.config])
    if args.backup_dir:
        cmd.extend(["-b", args.backup_dir])
    if args.full:
        cmd.extend(["--full"])
    if args.verbose:
        cmd.extend(["--verbose"])

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        logger.info("Local backup collection completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Local backup collection failed with exit code {e.returncode}")
        return False


def run_backup_external(args):
    """Run the backup-external tool with the given arguments."""
    logger.info("Starting external backup transfer phase...")

    cmd = ["backup-external"]

    # Pass through relevant arguments
    if args.config:
        cmd.extend(["-c", args.config])
    if args.backup_dir:
        cmd.extend(["-b", args.backup_dir])
    if args.destination:
        cmd.extend(["-d", args.destination])
    if args.verbose:
        cmd.extend(["--verbose"])

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        logger.info("External backup transfer completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"External backup transfer failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Complete backup system (both local and external phases)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1]
        if __doc__
        else ""
        if __doc__
        else "",  # Use the docstring as extended help
    )
    parser.add_argument(
        "-c", "--config", help=f"Path to config file (default: {DEFAULT_CONFIG_FILE})"
    )
    parser.add_argument(
        "-b",
        "--backup-dir",
        help=f"Backup directory (default: $DBACKUP or {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "-d", "--destination", help="External destination directory (overrides config)"
    )
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="Perform a full backup instead of incremental",
    )
    parser.add_argument(
        "--local-only", action="store_true", help="Only run the local backup phase"
    )
    parser.add_argument(
        "--external-only",
        action="store_true",
        help="Only run the external backup phase",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("--version", action="version", version="backup 1.0.0")
    args = parser.parse_args()

    # Set verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Ensure that --local-only and --external-only aren't used together
    if args.local_only and args.external_only:
        logger.error(
            "Cannot use --local-only and --external-only together. Choose one."
        )
        return 1

    success = True

    # Run local backup phase if requested or if neither --local-only nor --external-only specified
    if args.local_only or not args.external_only:
        if not run_backup_collect(args):
            success = False
            if not args.external_only:
                logger.warning(
                    "Local backup failed, but continuing to external backup phase..."
                )

    # Run external backup phase if requested or if neither --local-only nor --external-only specified
    if args.external_only or not args.local_only:
        if not run_backup_external(args):
            success = False

    if success:
        logger.info("Complete backup process finished successfully")
        return 0
    else:
        logger.error("Backup process completed with errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
