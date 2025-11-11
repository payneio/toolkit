#!/usr/bin/env python3
"""Schedule - Systemd timer and service management tool.

A tool to easily create, manage, and monitor systemd user timers and services
following best practices.

Usage:
    schedule list [--all]
    schedule add <name> --command <cmd> --schedule <schedule> [options]
    schedule remove <name> [--keep-logs]
    schedule status <name>
    schedule logs <name> [--follow] [--lines N]
    schedule enable <name>
    schedule disable <name>
    schedule start <name>
    schedule stop <name>

Examples:
    # List all user timers
    schedule list

    # Create a timer for ProtonMail sync every 5 minutes
    schedule add protonmail-sync \\
        --command "protonmail sync" \\
        --schedule "5min" \\
        --description "Sync ProtonMail emails" \\
        --env-file ~/.config/protonmail/env \\
        --condition-command "pgrep -f protonmail-bridge"

    # Create a daily backup timer at 2 AM
    schedule add daily-backup \\
        --command "backup run" \\
        --schedule "daily" \\
        --on-calendar "*-*-* 02:00:00"

    # Check status of a timer
    schedule status protonmail-sync

    # View logs in real-time
    schedule logs protonmail-sync --follow

    # Remove a timer
    schedule remove protonmail-sync
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_systemd_user_dir() -> Path:
    """Get the systemd user directory."""
    return Path.home() / ".config" / "systemd" / "user"


def run_systemctl(
    args: list[str], check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run systemctl command with user flag."""
    cmd = ["systemctl", "--user"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
    )


def list_timers(all_timers: bool = False) -> None:
    """List all user timers."""
    args = ["list-timers"]
    if all_timers:
        args.append("--all")

    result = run_systemctl(args, check=False)
    print(result.stdout)

    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def generate_service_content(
    name: str,
    command: str,
    description: str | None = None,
    env_file: str | None = None,
    condition_command: str | None = None,
    working_directory: str | None = None,
    environment: dict[str, str] | None = None,
) -> str:
    """Generate systemd service file content."""
    desc = description or f"{name} service"

    content = f"""[Unit]
Description={desc}
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
"""

    # Add default PATH
    content += 'Environment="PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin"\n'

    # Add additional environment variables
    if environment:
        for key, value in environment.items():
            content += f'Environment="{key}={value}"\n'

    # Add environment file if specified
    if env_file:
        content += f"EnvironmentFile={env_file}\n"

    content += "\n"

    # Add condition command if specified
    if condition_command:
        content += "# Pre-condition check\n"
        # Use double quotes to avoid conflicts with single quotes in the command
        escaped_condition = condition_command.replace('"', '\\"')
        content += f'ExecStartPre=/bin/bash -c "{escaped_condition}"\n\n'

    # Set working directory if specified
    if working_directory:
        content += f"WorkingDirectory={working_directory}\n"

    # Add the main command
    content += "# Run the command\n"
    # Use double quotes to avoid conflicts with single quotes in the command
    escaped_command = command.replace('"', '\\"')
    content += f'ExecStart=/bin/bash -c "{escaped_command}"\n\n'

    # Logging
    content += """# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier={name}

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=default.target
""".format(name=name)

    return content


def generate_timer_content(
    name: str,
    description: str | None = None,
    on_boot_sec: str = "1min",
    on_unit_active_sec: str | None = None,
    on_calendar: str | None = None,
    persistent: bool = False,
) -> str:
    """Generate systemd timer file content."""
    desc = description or f"{name} timer"

    content = f"""[Unit]
Description={desc}
Requires={name}.service

[Timer]
"""

    # Add boot delay
    if on_boot_sec:
        content += f"OnBootSec={on_boot_sec}\n"

    # Add interval-based schedule
    if on_unit_active_sec:
        content += f"OnUnitActiveSec={on_unit_active_sec}\n"

    # Add calendar-based schedule
    if on_calendar:
        content += f"OnCalendar={on_calendar}\n"

    content += f"""
# If the system was offline, {"run" if persistent else "don't run"} missed timers
Persistent={"true" if persistent else "false"}

[Install]
WantedBy=timers.target
"""

    return content


def parse_schedule(schedule: str) -> tuple[str | None, str | None]:
    """Parse schedule string into timer parameters.

    Returns:
        Tuple of (on_unit_active_sec, on_calendar)
    """
    schedule_lower = schedule.lower()

    # Simple interval schedules
    if any(
        schedule_lower.endswith(unit)
        for unit in ["min", "hour", "h", "day", "d", "week", "w"]
    ):
        return schedule, None

    # Daily at specific time
    if schedule_lower == "daily":
        return "1day", None

    # Hourly
    if schedule_lower == "hourly":
        return "1hour", None

    # Assume it's a calendar spec
    return None, schedule


def add_timer(args: argparse.Namespace) -> None:
    """Add a new systemd timer and service."""
    name = args.name
    command = args.command
    schedule = args.schedule

    # Parse schedule
    on_unit_active_sec, on_calendar = parse_schedule(schedule)

    if args.on_calendar:
        on_calendar = args.on_calendar
        on_unit_active_sec = None

    # Create systemd directory if it doesn't exist
    systemd_dir = get_systemd_user_dir()
    systemd_dir.mkdir(parents=True, exist_ok=True)

    # Generate service file
    environment = {}
    if args.environment:
        for env in args.environment:
            key, value = env.split("=", 1)
            environment[key] = value

    service_content = generate_service_content(
        name=name,
        command=command,
        description=args.description,
        env_file=args.env_file,
        condition_command=args.condition_command,
        working_directory=args.working_directory,
        environment=environment,
    )

    # Generate timer file
    timer_content = generate_timer_content(
        name=name,
        description=args.description,
        on_boot_sec=args.on_boot_sec,
        on_unit_active_sec=on_unit_active_sec,
        on_calendar=on_calendar,
        persistent=args.persistent,
    )

    # Write service file
    service_path = systemd_dir / f"{name}.service"
    timer_path = systemd_dir / f"{name}.timer"

    # Check if files already exist
    if service_path.exists() and not args.force:
        print(f"Error: Service file already exists: {service_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        sys.exit(1)

    if timer_path.exists() and not args.force:
        print(f"Error: Timer file already exists: {timer_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        sys.exit(1)

    # Write files
    service_path.write_text(service_content)
    timer_path.write_text(timer_content)

    print(f"Created service: {service_path}")
    print(f"Created timer: {timer_path}")

    # Reload systemd daemon
    print("\nReloading systemd daemon...")
    run_systemctl(["daemon-reload"])

    # Enable and start timer if requested
    if not args.no_enable:
        print(f"Enabling {name}.timer...")
        run_systemctl(["enable", f"{name}.timer"])

    if not args.no_start:
        print(f"Starting {name}.timer...")
        run_systemctl(["start", f"{name}.timer"])

    print(f"\n✓ Timer '{name}' created and started successfully!")

    # Warn about environment variables if not explicitly set in service
    if not environment and not args.env_file:
        print(
            "\n⚠️  Note: Systemd user units don't inherit shell environment variables."
        )
        print("   If your command needs environment variables, pass them with:")
        print(f"     schedule add {name} --command '...' -e VAR=value")

    print("\nUseful commands:")
    print(f"  Status:  schedule status {name}")
    print(f"  Logs:    schedule logs {name} --follow")
    print(f"  Disable: schedule disable {name}")
    print(f"  Remove:  schedule remove {name}")


def remove_timer(args: argparse.Namespace) -> None:
    """Remove a systemd timer and service."""
    name = args.name
    systemd_dir = get_systemd_user_dir()

    service_path = systemd_dir / f"{name}.service"
    timer_path = systemd_dir / f"{name}.timer"

    # Check if files exist
    if not service_path.exists() and not timer_path.exists():
        print(f"Error: Timer '{name}' not found", file=sys.stderr)
        sys.exit(1)

    # Stop and disable timer
    print(f"Stopping {name}.timer...")
    run_systemctl(["stop", f"{name}.timer"], check=False)

    print(f"Disabling {name}.timer...")
    run_systemctl(["disable", f"{name}.timer"], check=False)

    # Remove files
    if timer_path.exists():
        timer_path.unlink()
        print(f"Removed: {timer_path}")

    if service_path.exists():
        service_path.unlink()
        print(f"Removed: {service_path}")

    # Reload systemd daemon
    print("\nReloading systemd daemon...")
    run_systemctl(["daemon-reload"])

    # Clear logs if requested
    if not args.keep_logs:
        print(f"Clearing logs for {name}...")
        subprocess.run(
            ["journalctl", "--user", "--vacuum-time=1s", "-u", name],
            check=False,
            capture_output=True,
        )

    print(f"\n✓ Timer '{name}' removed successfully!")


def status_timer(args: argparse.Namespace) -> None:
    """Show status of a timer and its service."""
    name = args.name

    print("=== Timer Status ===")
    result = run_systemctl(["status", f"{name}.timer"], check=False)
    print(result.stdout)

    print("\n=== Service Status ===")
    result = run_systemctl(["status", f"{name}.service"], check=False)
    print(result.stdout)

    print("\n=== Next Scheduled Run ===")
    result = run_systemctl(["list-timers", f"{name}.timer"], check=False)
    print(result.stdout)


def logs_timer(args: argparse.Namespace) -> None:
    """Show logs for a service."""
    name = args.name
    cmd = ["journalctl", "--user", "-u", name]

    if args.follow:
        cmd.append("-f")

    if args.lines:
        cmd.extend(["-n", str(args.lines)])

    if args.since:
        cmd.extend(["--since", args.since])

    # Run journalctl directly (don't capture output)
    subprocess.run(cmd)


def enable_timer(args: argparse.Namespace) -> None:
    """Enable a timer."""
    name = args.name
    print(f"Enabling {name}.timer...")
    run_systemctl(["enable", f"{name}.timer"])
    print(f"✓ Timer '{name}' enabled")


def disable_timer(args: argparse.Namespace) -> None:
    """Disable a timer."""
    name = args.name
    print(f"Disabling {name}.timer...")
    run_systemctl(["disable", f"{name}.timer"])
    print(f"✓ Timer '{name}' disabled")


def start_timer(args: argparse.Namespace) -> None:
    """Start a timer."""
    name = args.name
    print(f"Starting {name}.timer...")
    run_systemctl(["start", f"{name}.timer"])
    print(f"✓ Timer '{name}' started")


def stop_timer(args: argparse.Namespace) -> None:
    """Stop a timer."""
    name = args.name
    print(f"Stopping {name}.timer...")
    run_systemctl(["stop", f"{name}.timer"])
    print(f"✓ Timer '{name}' stopped")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage systemd user timers and services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List all user timers")
    list_parser.add_argument(
        "--all", action="store_true", help="Show all timers including inactive"
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new timer")
    add_parser.add_argument("name", help="Name of the timer/service")
    add_parser.add_argument("--command", required=True, help="Command to execute")
    add_parser.add_argument(
        "--schedule",
        required=True,
        help="Schedule (e.g., '5min', 'hourly', 'daily', '1h')",
    )
    add_parser.add_argument("--description", help="Description of the timer/service")
    add_parser.add_argument(
        "--env-file", help="Path to environment file (e.g., ~/.config/app/env)"
    )
    add_parser.add_argument(
        "--environment",
        "-e",
        action="append",
        help="Environment variable (KEY=VALUE)",
    )
    add_parser.add_argument(
        "--condition-command",
        help="Command that must succeed before running (e.g., 'pgrep myapp')",
    )
    add_parser.add_argument(
        "--working-directory", help="Working directory for the command"
    )
    add_parser.add_argument(
        "--on-boot-sec", default="1min", help="Delay after boot (default: 1min)"
    )
    add_parser.add_argument(
        "--on-calendar",
        help="Calendar-based schedule (e.g., '*-*-* 02:00:00' for 2 AM daily)",
    )
    add_parser.add_argument(
        "--persistent",
        action="store_true",
        help="Run missed timers if system was offline",
    )
    add_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing timer/service"
    )
    add_parser.add_argument(
        "--no-enable", action="store_true", help="Don't enable the timer"
    )
    add_parser.add_argument(
        "--no-start", action="store_true", help="Don't start the timer"
    )

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a timer")
    remove_parser.add_argument("name", help="Name of the timer/service")
    remove_parser.add_argument(
        "--keep-logs", action="store_true", help="Keep service logs"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show timer status")
    status_parser.add_argument("name", help="Name of the timer/service")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show service logs")
    logs_parser.add_argument("name", help="Name of the timer/service")
    logs_parser.add_argument(
        "--follow", "-f", action="store_true", help="Follow logs in real-time"
    )
    logs_parser.add_argument("--lines", "-n", type=int, help="Number of lines to show")
    logs_parser.add_argument("--since", help="Show logs since (e.g., 'today', '1h')")

    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable a timer")
    enable_parser.add_argument("name", help="Name of the timer")

    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable a timer")
    disable_parser.add_argument("name", help="Name of the timer")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start a timer")
    start_parser.add_argument("name", help="Name of the timer")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a timer")
    stop_parser.add_argument("name", help="Name of the timer")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    # Route to appropriate function
    commands = {
        "list": list_timers,
        "add": add_timer,
        "remove": remove_timer,
        "status": status_timer,
        "logs": logs_timer,
        "enable": enable_timer,
        "disable": disable_timer,
        "start": start_timer,
        "stop": stop_timer,
    }

    commands[args.subcommand](args)


if __name__ == "__main__":
    main()
