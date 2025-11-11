"""Tests for schedule tool."""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.system import schedule


class TestSchedule(unittest.TestCase):
    """Test schedule functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_home = Path("/home/testuser")
        self.systemd_dir = self.test_home / ".config" / "systemd" / "user"

    @patch("tools.system.schedule.Path.home")
    def test_get_systemd_user_dir(self, mock_home: MagicMock) -> None:
        """Test getting systemd user directory."""
        mock_home.return_value = self.test_home
        result = schedule.get_systemd_user_dir()
        self.assertEqual(result, self.systemd_dir)

    @patch("tools.system.schedule.subprocess.run")
    def test_run_systemctl(self, mock_run: MagicMock) -> None:
        """Test running systemctl commands."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["systemctl", "--user", "status"],
            returncode=0,
            stdout="Active: active",
            stderr="",
        )

        result = schedule.run_systemctl(["status"])

        mock_run.assert_called_once_with(
            ["systemctl", "--user", "status"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout, "Active: active")

    def test_generate_service_content_basic(self) -> None:
        """Test generating basic service content."""
        content = schedule.generate_service_content(
            name="test-service", command="echo hello"
        )

        self.assertIn("[Unit]", content)
        self.assertIn("Description=test-service service", content)
        self.assertIn("[Service]", content)
        self.assertIn("Type=oneshot", content)
        self.assertIn('ExecStart=/bin/bash -c "echo hello"', content)
        self.assertIn("StandardOutput=journal", content)
        self.assertIn("NoNewPrivileges=yes", content)
        self.assertIn("[Install]", content)

    def test_generate_service_content_with_options(self) -> None:
        """Test generating service content with all options."""
        content = schedule.generate_service_content(
            name="test-service",
            command="echo hello",
            description="Test service",
            env_file="/home/user/.config/test/env",
            condition_command="pgrep test-app",
            working_directory="/home/user/work",
            environment={"KEY1": "value1", "KEY2": "value2"},
        )

        self.assertIn("Description=Test service", content)
        self.assertIn("EnvironmentFile=/home/user/.config/test/env", content)
        self.assertIn('ExecStartPre=/bin/bash -c "pgrep test-app"', content)
        self.assertIn("WorkingDirectory=/home/user/work", content)
        self.assertIn('Environment="KEY1=value1"', content)
        self.assertIn('Environment="KEY2=value2"', content)

    def test_generate_timer_content_basic(self) -> None:
        """Test generating basic timer content."""
        content = schedule.generate_timer_content(
            name="test-timer", on_unit_active_sec="5min"
        )

        self.assertIn("[Unit]", content)
        self.assertIn("Description=test-timer timer", content)
        self.assertIn("Requires=test-timer.service", content)
        self.assertIn("[Timer]", content)
        self.assertIn("OnBootSec=1min", content)
        self.assertIn("OnUnitActiveSec=5min", content)
        self.assertIn("Persistent=false", content)
        self.assertIn("WantedBy=timers.target", content)

    def test_generate_timer_content_calendar(self) -> None:
        """Test generating timer content with calendar schedule."""
        content = schedule.generate_timer_content(
            name="test-timer", on_calendar="*-*-* 02:00:00", persistent=True
        )

        self.assertIn("OnCalendar=*-*-* 02:00:00", content)
        self.assertIn("Persistent=true", content)

    def test_parse_schedule_interval(self) -> None:
        """Test parsing interval-based schedules."""
        test_cases = [
            ("5min", ("5min", None)),
            ("1hour", ("1hour", None)),
            ("30min", ("30min", None)),
            ("1day", ("1day", None)),
            ("daily", ("1day", None)),
            ("hourly", ("1hour", None)),
        ]

        for schedule_str, expected in test_cases:
            result = schedule.parse_schedule(schedule_str)
            self.assertEqual(result, expected)

    def test_parse_schedule_calendar(self) -> None:
        """Test parsing calendar-based schedules."""
        schedule_str = "*-*-* 02:00:00"
        result = schedule.parse_schedule(schedule_str)
        self.assertEqual(result, (None, schedule_str))

    @patch("tools.system.schedule.run_systemctl")
    @patch("tools.system.schedule.get_systemd_user_dir")
    @patch("tools.system.schedule.Path.write_text")
    @patch("tools.system.schedule.Path.exists")
    @patch("tools.system.schedule.Path.mkdir")
    def test_add_timer(
        self,
        mock_mkdir: MagicMock,
        mock_exists: MagicMock,
        mock_write_text: MagicMock,
        mock_get_dir: MagicMock,
        mock_systemctl: MagicMock,
    ) -> None:
        """Test adding a new timer."""
        mock_get_dir.return_value = self.systemd_dir
        mock_exists.return_value = False

        args = MagicMock()
        args.name = "test-timer"
        args.command = "echo hello"
        args.schedule = "5min"
        args.description = "Test timer"
        args.env_file = None
        args.environment = None
        args.condition_command = None
        args.working_directory = None
        args.on_boot_sec = "1min"
        args.on_calendar = None
        args.persistent = False
        args.force = False
        args.no_enable = False
        args.no_start = False

        with patch("builtins.print"):
            schedule.add_timer(args)

        # Verify systemctl calls
        self.assertEqual(mock_systemctl.call_count, 3)
        mock_systemctl.assert_any_call(["daemon-reload"])
        mock_systemctl.assert_any_call(["enable", "test-timer.timer"])
        mock_systemctl.assert_any_call(["start", "test-timer.timer"])

    @patch("tools.system.schedule.run_systemctl")
    @patch("tools.system.schedule.subprocess.run")
    @patch("tools.system.schedule.get_systemd_user_dir")
    @patch("tools.system.schedule.Path.exists")
    @patch("tools.system.schedule.Path.unlink")
    def test_remove_timer(
        self,
        mock_unlink: MagicMock,
        mock_exists: MagicMock,
        mock_get_dir: MagicMock,
        mock_subprocess: MagicMock,
        mock_systemctl: MagicMock,
    ) -> None:
        """Test removing a timer."""
        mock_get_dir.return_value = self.systemd_dir
        mock_exists.return_value = True

        args = MagicMock()
        args.name = "test-timer"
        args.keep_logs = True

        with patch("builtins.print"):
            schedule.remove_timer(args)

        # Verify systemctl calls
        mock_systemctl.assert_any_call(["stop", "test-timer.timer"], check=False)
        mock_systemctl.assert_any_call(["disable", "test-timer.timer"], check=False)
        mock_systemctl.assert_any_call(["daemon-reload"])

        # Verify files were removed
        self.assertEqual(mock_unlink.call_count, 2)

    @patch("tools.system.schedule.run_systemctl")
    def test_list_timers(self, mock_systemctl: MagicMock) -> None:
        """Test listing timers."""
        mock_systemctl.return_value = subprocess.CompletedProcess(
            args=["systemctl", "--user", "list-timers"],
            returncode=0,
            stdout="NEXT LEFT LAST PASSED UNIT",
            stderr="",
        )

        with patch("builtins.print"):
            schedule.list_timers(all_timers=False)

        mock_systemctl.assert_called_once_with(["list-timers"], check=False)

    @patch("tools.system.schedule.run_systemctl")
    def test_status_timer(self, mock_systemctl: MagicMock) -> None:
        """Test getting timer status."""
        mock_systemctl.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Active: active",
            stderr="",
        )

        args = MagicMock()
        args.name = "test-timer"

        with patch("builtins.print"):
            schedule.status_timer(args)

        # Should call status for timer, service, and list-timers
        self.assertEqual(mock_systemctl.call_count, 3)
        mock_systemctl.assert_any_call(["status", "test-timer.timer"], check=False)
        mock_systemctl.assert_any_call(["status", "test-timer.service"], check=False)
        mock_systemctl.assert_any_call(["list-timers", "test-timer.timer"], check=False)

    @patch("tools.system.schedule.subprocess.run")
    def test_logs_timer(self, mock_run: MagicMock) -> None:
        """Test viewing timer logs."""
        args = MagicMock()
        args.name = "test-timer"
        args.follow = True
        args.lines = 50
        args.since = "today"

        schedule.logs_timer(args)

        mock_run.assert_called_once_with(
            [
                "journalctl",
                "--user",
                "-u",
                "test-timer",
                "-f",
                "-n",
                "50",
                "--since",
                "today",
            ]
        )

    @patch("tools.system.schedule.run_systemctl")
    def test_enable_timer(self, mock_systemctl: MagicMock) -> None:
        """Test enabling a timer."""
        args = MagicMock()
        args.name = "test-timer"

        with patch("builtins.print"):
            schedule.enable_timer(args)

        mock_systemctl.assert_called_once_with(["enable", "test-timer.timer"])

    @patch("tools.system.schedule.run_systemctl")
    def test_disable_timer(self, mock_systemctl: MagicMock) -> None:
        """Test disabling a timer."""
        args = MagicMock()
        args.name = "test-timer"

        with patch("builtins.print"):
            schedule.disable_timer(args)

        mock_systemctl.assert_called_once_with(["disable", "test-timer.timer"])

    @patch("tools.system.schedule.run_systemctl")
    def test_start_timer(self, mock_systemctl: MagicMock) -> None:
        """Test starting a timer."""
        args = MagicMock()
        args.name = "test-timer"

        with patch("builtins.print"):
            schedule.start_timer(args)

        mock_systemctl.assert_called_once_with(["start", "test-timer.timer"])

    @patch("tools.system.schedule.run_systemctl")
    def test_stop_timer(self, mock_systemctl: MagicMock) -> None:
        """Test stopping a timer."""
        args = MagicMock()
        args.name = "test-timer"

        with patch("builtins.print"):
            schedule.stop_timer(args)

        mock_systemctl.assert_called_once_with(["stop", "test-timer.timer"])


if __name__ == "__main__":
    unittest.main()
