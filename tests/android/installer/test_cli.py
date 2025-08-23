"""Tests for Android installer CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ovmobilebench.android.installer.cli import app


class TestAndroidInstallerCLI:
    """Test Android installer CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sdk_root = Path(self.tmpdir.name) / "android-sdk"

    def teardown_method(self):
        """Clean up test environment."""
        self.tmpdir.cleanup()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Android SDK/NDK installation" in result.stdout

    @patch("ovmobilebench.android.installer.cli.get_recommended_settings")
    def test_list_targets_command(self, mock_settings):
        """Test list-targets command."""
        mock_settings.return_value = {
            "api": 30,
            "target": "google_atd",
            "arch": "x86_64",
        }
        result = self.runner.invoke(app, ["list-targets"])
        assert result.exit_code == 0
        assert "API" in result.stdout or "Supported" in result.stdout

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_command_basic(self, mock_ensure):
        """Test basic install command."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": self.sdk_root / "ndk" / "r26d",
            "installed_components": ["platform-tools", "platforms;android-30"],
            "avd_created": "test_avd",
        }

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30"],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()
        assert "Installation complete" in result.stdout or "Success" in result.stdout

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_command_with_ndk(self, mock_ensure):
        """Test install command with NDK."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": self.sdk_root / "ndk" / "r26d",
            "installed_components": ["ndk;26.1.10909125"],
            "avd_created": None,
        }

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--ndk", "r26d"],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_command_dry_run(self, mock_ensure):
        """Test install command with dry run."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": None,
            "installed_components": [],
            "avd_created": None,
            "dry_run": True,
        }

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--dry-run"],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()
        # Dry run shows configuration table with "Dry Run" row set to "Yes"
        assert "Dry Run" in result.stdout

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_command_with_error(self, mock_ensure):
        """Test install command with error."""
        from ovmobilebench.android.installer.errors import InstallerError

        mock_ensure.side_effect = InstallerError("Test error")

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30"],
        )

        assert result.exit_code != 0
        assert "Error" in result.stdout or "error" in result.stdout.lower()

    @patch("ovmobilebench.android.installer.cli.verify_installation")
    def test_verify_command(self, mock_verify):
        """Test verify command."""
        mock_verify.return_value = {
            "sdk_root_exists": True,
            "cmdline_tools": True,
            "platform_tools": True,
            "emulator": True,
            "ndk": True,
            "ndk_versions": ["r26d"],
            "avds": [],
            "components": ["platform-tools", "emulator"],
        }

        result = self.runner.invoke(app, ["verify", "--sdk-root", str(self.sdk_root)])

        assert result.exit_code == 0
        mock_verify.assert_called_once()
        assert "Installation Status" in result.stdout or "Verifying installation" in result.stdout

    @patch("ovmobilebench.android.installer.cli.verify_installation")
    def test_verify_command_nothing_installed(self, mock_verify):
        """Test verify command when nothing is installed."""
        mock_verify.return_value = {
            "sdk_root_exists": True,
            "cmdline_tools": False,
            "platform_tools": False,
            "emulator": False,
            "ndk": False,
            "ndk_versions": [],
            "avds": [],
            "components": [],
        }

        result = self.runner.invoke(app, ["verify", "--sdk-root", str(self.sdk_root)])

        assert result.exit_code == 0
        assert "Not installed" in result.stdout or "None" in result.stdout

    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(app, ["--help"])
        # With --help flag, should exit cleanly with code 0
        assert result.exit_code == 0
        assert "Android SDK/NDK installation" in result.stdout
        # Commands should be shown in the output
        assert "setup" in result.stdout.lower()
        assert "verify" in result.stdout.lower()

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_with_avd(self, mock_ensure):
        """Test setup command with AVD creation."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": None,
            "installed_components": ["system-images;android-30;google_atd;x86_64"],
            "avd_created": "test_avd",
        }

        result = self.runner.invoke(
            app,
            [
                "setup",
                "--sdk-root",
                str(self.sdk_root),
                "--api",
                "30",
                "--create-avd",
                "test_avd",
            ],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_verbose(self, mock_ensure):
        """Test setup command with verbose output."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": None,
            "installed_components": [],
            "avd_created": None,
        }

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--verbose"],
        )

        assert result.exit_code == 0
        # Verbose flag should be passed
        call_kwargs = mock_ensure.call_args[1]
        assert "verbose" in call_kwargs

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_with_jsonl(self, mock_ensure):
        """Test setup command with JSON Lines output."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": None,
            "installed_components": [],
            "avd_created": None,
        }

        jsonl_path = Path(self.tmpdir.name) / "install.jsonl"
        result = self.runner.invoke(
            app,
            [
                "setup",
                "--sdk-root",
                str(self.sdk_root),
                "--api",
                "30",
                "--jsonl-log",
                str(jsonl_path),
            ],
        )

        assert result.exit_code == 0
        # JSONL path should be passed
        call_kwargs = mock_ensure.call_args[1]
        assert "jsonl_log" in call_kwargs

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_with_force(self, mock_ensure):
        """Test setup command basic without optional features."""
        mock_ensure.return_value = {
            "sdk_root": self.sdk_root,
            "ndk_path": None,
            "installed_components": [],
            "avd_created": None,
        }

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30"],
        )

        assert result.exit_code == 0
        # Ensure the function was called
        mock_ensure.assert_called_once()
