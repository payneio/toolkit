#!/usr/bin/env python3
"""
protonmail: Access and manage ProtonMail emails via Bridge

Access your ProtonMail inbox through the ProtonMail Bridge using IMAP/SMTP.
Requires ProtonMail Bridge to be installed and running.

Usage: protonmail [options] [command]

Commands:
  list [folder]       List emails (default: INBOX)
  read <message_id>   Read a specific email by ID
  send               Send a new email (interactive)
  search <query>     Search emails by subject or sender

Examples:
  protonmail list              # List emails in INBOX
  protonmail list Sent        # List emails in Sent folder
  protonmail read 42          # Read email with ID 42
  protonmail search "invoice" # Search for emails with "invoice" in subject
  protonmail send             # Send a new email (interactive)
"""

import sys
import os
import argparse
import imaplib
import email
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
import configparser

# Default configuration
DEFAULT_CONFIG = {
    "IMAP": {
        "hostname": "127.0.0.1",
        "port": 1143,
        "username": "paul@payne.io",
        "password": "$PROTONMAIL_API_KEY",
        "security": "STARTTLS",
    },
    "SMTP": {
        "hostname": "127.0.0.1",
        "port": 1025,
        "username": "paul@payne.io",
        "password": "$PROTONMAIL_API_KEY",
        "security": "STARTTLS",
    },
}


def load_config():
    """Load configuration from file or use defaults."""
    config_path = os.path.expanduser("~/.config/protonmail/config.ini")
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(config_path):
        parser = configparser.ConfigParser()
        parser.read(config_path)

        # Update config with values from file
        for section in parser.sections():
            if section in config:
                for key, value in parser.items(section):
                    if key in config[section]:
                        # Convert port to int
                        if key == "port":
                            config[section][key] = int(value)
                        else:
                            config[section][key] = value

    return config


def setup_config():
    """Create initial configuration file."""
    config_path = os.path.expanduser("~/.config/protonmail/config.ini")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Create config parser and add default values
    config = configparser.ConfigParser()
    for section, options in DEFAULT_CONFIG.items():
        config[section] = {}
        for key, value in options.items():
            config[section][key] = str(value)

    # Write to file
    with open(config_path, "w") as f:
        config.write(f)

    print(f"Configuration file created at {config_path}")
    print("Please edit this file to update your credentials.")
    return DEFAULT_CONFIG


def connect_imap(config):
    """Connect to IMAP server."""
    imap_config = config["IMAP"]

    # Create connection
    if imap_config["security"] == "SSL/TLS":
        imap = imaplib.IMAP4_SSL(imap_config["hostname"], imap_config["port"])
    else:
        imap = imaplib.IMAP4(imap_config["hostname"], imap_config["port"])
        if imap_config["security"] == "STARTTLS":
            imap.starttls()

    # Login
    imap.login(imap_config["username"], imap_config["password"])
    return imap


def list_folders(imap):
    """List all available folders."""
    status, folders = imap.list()
    if status != "OK":
        print("Failed to retrieve folders")
        return []

    folder_list = []
    for folder in folders:
        folder_parts = folder.decode().split(' "/"')
        if len(folder_parts) > 1:
            folder_name = folder_parts[-1].strip().strip('"')
            folder_list.append(folder_name)

    return folder_list


def list_emails(config, folder="INBOX", limit=20):
    """List emails in the specified folder."""
    try:
        imap = connect_imap(config)

        # Select folder
        status, data = imap.select(folder)
        if status != "OK":
            print(f"Error: Could not select folder '{folder}'")
            print(f"Available folders: {', '.join(list_folders(imap))}")
            imap.logout()
            return

        # Get message IDs
        status, data = imap.search(None, "ALL")
        if status != "OK":
            print(f"Error: Could not search folder '{folder}'")
            imap.logout()
            return

        message_ids = data[0].split()
        if not message_ids:
            print(f"No emails found in {folder}")
            imap.logout()
            return

        # Start from the end (most recent)
        start_index = max(0, len(message_ids) - limit)
        message_ids = message_ids[start_index:]

        # Display emails
        print(
            f"Recent emails in {folder} (showing {len(message_ids)} of {len(data[0].split())}):"
        )
        print("-" * 70)

        for msg_id in reversed(message_ids):  # Reversed to show newest first
            status, data = imap.fetch(
                msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
            )
            if status != "OK":
                continue

            header_data = data[0][1].decode("utf-8", errors="ignore")
            msg = email.message_from_string(header_data)

            date = msg.get("Date", "No date")
            sender = msg.get("From", "No sender")
            subject = msg.get("Subject", "No subject")

            # Format output
            print(f"ID: {msg_id.decode()}")
            print(f"From: {sender}")
            print(f"Date: {date}")
            print(f"Subject: {subject}")
            print("-" * 70)

        imap.logout()

    except Exception as e:
        print(f"Error: {str(e)}")
        return


def read_email(config, message_id):
    """Read a specific email by ID."""
    try:
        imap = connect_imap(config)

        # Select INBOX
        imap.select("INBOX")

        # Fetch the email
        status, data = imap.fetch(message_id.encode(), "(RFC822)")
        if status != "OK":
            print(f"Error: Could not fetch email with ID {message_id}")
            imap.logout()
            return

        # Parse the email
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Print header information
        print("-" * 70)
        print(f"From: {msg.get('From', 'No sender')}")
        print(f"To: {msg.get('To', 'No recipient')}")
        print(f"Date: {msg.get('Date', 'No date')}")
        print(f"Subject: {msg.get('Subject', 'No subject')}")
        print("-" * 70)

        # Print body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode(
                        "utf-8", errors="ignore"
                    )
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        print(body)
        print("-" * 70)

        imap.logout()

    except Exception as e:
        print(f"Error: {str(e)}")
        return


def search_emails(config, query, folder="INBOX"):
    """Search emails by subject or sender."""
    try:
        imap = connect_imap(config)

        # Select folder
        status, data = imap.select(folder)
        if status != "OK":
            print(f"Error: Could not select folder '{folder}'")
            imap.logout()
            return

        # Search by subject or sender
        status, subject_data = imap.search(None, f'SUBJECT "{query}"')
        status, from_data = imap.search(None, f'FROM "{query}"')

        message_ids = set(subject_data[0].split() + from_data[0].split())
        if not message_ids:
            print(f"No emails found matching '{query}'")
            imap.logout()
            return

        # Display emails
        print(f"Emails matching '{query}' in {folder}:")
        print("-" * 70)

        for msg_id in reversed(
            sorted(message_ids)
        ):  # Sort and reverse for consistent order
            status, data = imap.fetch(
                msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
            )
            if status != "OK":
                continue

            header_data = data[0][1].decode("utf-8", errors="ignore")
            msg = email.message_from_string(header_data)

            date = msg.get("Date", "No date")
            sender = msg.get("From", "No sender")
            subject = msg.get("Subject", "No subject")

            # Format output
            print(f"ID: {msg_id.decode()}")
            print(f"From: {sender}")
            print(f"Date: {date}")
            print(f"Subject: {subject}")
            print("-" * 70)

        imap.logout()

    except Exception as e:
        print(f"Error: {str(e)}")
        return


def send_email(config):
    """Send a new email interactively."""
    try:
        # Get email details
        to_email = input("To: ")
        subject = input("Subject: ")
        print("Message (end with a line containing only '.' or Ctrl+D):")

        # Collect message body
        body_lines = []
        while True:
            try:
                line = input()
                if line == ".":
                    break
                body_lines.append(line)
            except EOFError:
                break

        body = "\n".join(body_lines)

        # Create message
        msg = EmailMessage()
        msg["From"] = config["SMTP"]["username"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=config["SMTP"]["username"].split("@")[-1])
        msg.set_content(body)

        # Connect to SMTP server
        smtp_config = config["SMTP"]
        if smtp_config["security"] == "SSL/TLS":
            smtp = smtplib.SMTP_SSL(smtp_config["hostname"], smtp_config["port"])
        else:
            smtp = smtplib.SMTP(smtp_config["hostname"], smtp_config["port"])
            if smtp_config["security"] == "STARTTLS":
                smtp.starttls()

        # Login and send
        smtp.login(smtp_config["username"], smtp_config["password"])
        smtp.send_message(msg)
        smtp.quit()

        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Access and manage ProtonMail emails via Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1],
    )

    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List emails")
    list_parser.add_argument(
        "folder", nargs="?", default="INBOX", help="Folder to list (default: INBOX)"
    )
    list_parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=20,
        help="Number of emails to show (default: 20)",
    )

    # Read command
    read_parser = subparsers.add_parser("read", help="Read an email")
    read_parser.add_argument("message_id", help="ID of the message to read")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for emails")
    search_parser.add_argument("query", help="Search term (subject or sender)")
    search_parser.add_argument(
        "-f", "--folder", default="INBOX", help="Folder to search (default: INBOX)"
    )

    # Version argument
    parser.add_argument("-v", "--version", action="version", version="protonmail 1.0.0")

    # Parse arguments
    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Process commands
    if args.command == "list":
        list_emails(config, args.folder, args.limit)
    elif args.command == "read":
        read_email(config, args.message_id)
    elif args.command == "search":
        search_emails(config, args.query, args.folder)
    elif args.command == "send":
        send_email(config)
    elif args.command == "setup":
        setup_config()
    else:
        # Default to list if no command provided
        list_emails(config)

    return 0


if __name__ == "__main__":
    sys.exit(main())
