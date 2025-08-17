"""Tests for Android installer CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

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
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=self.sdk_root / "ndk" / "r26d",
            installed_components=["platform-tools", "platforms;android-30"],
            avd_created="test_avd",
        )

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30"],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()
        assert "Setup completed" in result.stdout or "Success" in result.stdout

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_command_with_ndk(self, mock_ensure):
        """Test install command with NDK."""
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=self.sdk_root / "ndk" / "r26d",
            installed_components=["ndk;26.1.10909125"],
            avd_created=None,
        )

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--ndk", "r26d"],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_command_dry_run(self, mock_ensure):
        """Test install command with dry run."""
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=None,
            installed_components=[],
            avd_created=None,
            dry_run=True,
        )

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--dry-run"],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()
        assert "DRY RUN" in result.stdout or "Would" in result.stdout

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
            "sdk_root": str(self.sdk_root),
            "cmdline_tools": True,
            "platform_tools": True,
            "platforms": ["android-30"],
            "system_images": [],
            "ndk_versions": ["r26d"],
            "avds": [],
        }

        result = self.runner.invoke(app, ["verify", "--sdk-root", str(self.sdk_root)])

        assert result.exit_code == 0
        mock_verify.assert_called_once()
        assert "Android SDK" in result.stdout or "Verification" in result.stdout

    @patch("ovmobilebench.android.installer.cli.verify_installation")
    def test_verify_command_nothing_installed(self, mock_verify):
        """Test verify command when nothing is installed."""
        mock_verify.return_value = {
            "sdk_root": str(self.sdk_root),
            "cmdline_tools": False,
            "platform_tools": False,
            "platforms": [],
            "system_images": [],
            "ndk_versions": [],
            "avds": [],
        }

        result = self.runner.invoke(app, ["verify", "--sdk-root", str(self.sdk_root)])

        assert result.exit_code == 0
        assert "not found" in result.stdout.lower() or "No" in result.stdout

    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(app, [])
        assert result.exit_code == 0
        assert "setup" in result.stdout
        assert "verify" in result.stdout

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_with_avd(self, mock_ensure):
        """Test setup command with AVD creation."""
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=None,
            installed_components=["system-images;android-30;google_atd;x86_64"],
            avd_created="test_avd",
        )

        result = self.runner.invoke(
            app,
            [
                "setup",
                "--sdk-root",
                str(self.sdk_root),
                "--api",
                "30",
                "--create-avd",
                "--avd-name",
                "test_avd",
            ],
        )

        assert result.exit_code == 0
        mock_ensure.assert_called_once()

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_verbose(self, mock_ensure):
        """Test setup command with verbose output."""
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=None,
            installed_components=[],
            avd_created=None,
        )

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
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=None,
            installed_components=[],
            avd_created=None,
        )

        jsonl_path = Path(self.tmpdir.name) / "install.jsonl"
        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--jsonl", str(jsonl_path)],
        )

        assert result.exit_code == 0
        # JSONL path should be passed
        call_kwargs = mock_ensure.call_args[1]
        assert "jsonl_path" in call_kwargs

    @patch("ovmobilebench.android.installer.cli.ensure_android_tools")
    def test_setup_with_force(self, mock_ensure):
        """Test setup command with force reinstall."""
        mock_ensure.return_value = Mock(
            sdk_root=self.sdk_root,
            ndk_path=None,
            installed_components=[],
            avd_created=None,
        )

        result = self.runner.invoke(
            app,
            ["setup", "--sdk-root", str(self.sdk_root), "--api", "30", "--force"],
        )

        assert result.exit_code == 0
        # Force flag should be passed
        call_kwargs = mock_ensure.call_args[1]
        assert "force" in call_kwargs
