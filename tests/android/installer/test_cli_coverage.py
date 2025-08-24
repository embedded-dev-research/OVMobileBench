"""Additional tests for CLI coverage gaps."""

import os
import tempfile
from unittest.mock import patch

from typer.testing import CliRunner

from ovmobilebench.android.installer import cli as installer_cli


class TestCLIAdditionalCoverage:
    """Test remaining gaps in installer CLI."""

    def test_setup_android_verbose_logging(self):
        """Test setup-android with verbose flag."""
        with patch("ovmobilebench.android.installer.cli.ensure_android_tools") as mock_ensure:
            with patch(
                "ovmobilebench.android.installer.cli.get_recommended_settings"
            ) as mock_settings:
                mock_settings.return_value = {"arch": "arm64-v8a"}
                mock_ensure.return_value = {
                    "sdk_root": "/test/sdk",
                    "ndk_path": "/test/ndk",
                    "installed": [],
                }

                # Use typer's testing interface
                runner = CliRunner()

                runner.invoke(
                    installer_cli.app,
                    ["setup", "--ndk", "r26d", "--api", "30", "--verbose"],
                )

                # Verify ensure_android_tools was called with verbose
                assert mock_ensure.called
                call_kwargs = mock_ensure.call_args.kwargs
                assert call_kwargs["verbose"] is True

    def test_setup_android_with_jsonl(self):
        """Test setup-android with JSONL output."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            jsonl_path = f.name

        try:
            with patch("ovmobilebench.android.installer.cli.ensure_android_tools") as mock_ensure:
                with patch(
                    "ovmobilebench.android.installer.cli.get_recommended_settings"
                ) as mock_settings:
                    mock_settings.return_value = {"arch": "arm64-v8a"}
                    mock_ensure.return_value = {
                        "sdk_root": "/test/sdk",
                        "ndk_path": "/test/ndk",
                        "installed": [],
                    }

                    # Use typer's testing interface
                    runner = CliRunner()

                    runner.invoke(
                        installer_cli.app,
                        ["setup", "--ndk", "r26d", "--api", "30", "--jsonl-log", jsonl_path],
                    )

                    # Verify ensure_android_tools was called with jsonl_log
                    assert mock_ensure.called
                    call_kwargs = mock_ensure.call_args.kwargs
                    assert str(call_kwargs["jsonl_log"]) == jsonl_path
        finally:
            if os.path.exists(jsonl_path):
                os.unlink(jsonl_path)

    def test_setup_android_with_force(self):
        """Test setup-android with accept-licenses flag."""
        with patch("ovmobilebench.android.installer.cli.ensure_android_tools") as mock_ensure:
            with patch(
                "ovmobilebench.android.installer.cli.get_recommended_settings"
            ) as mock_settings:
                mock_settings.return_value = {"arch": "arm64-v8a"}
                mock_ensure.return_value = {
                    "sdk_root": "/test/sdk",
                    "ndk_path": "/test/ndk",
                    "installed": [],
                }

                # Use typer's testing interface
                runner = CliRunner()

                runner.invoke(
                    installer_cli.app,
                    ["setup", "--ndk", "r26d", "--api", "30", "--accept-licenses"],
                )

                # Verify ensure_android_tools was called with accept_licenses
                assert mock_ensure.called
                call_kwargs = mock_ensure.call_args.kwargs
                assert call_kwargs["accept_licenses"] is True

    def test_verify_android_verbose(self):
        """Test verify command with verbose output."""
        with patch("ovmobilebench.android.installer.cli.verify_installation") as mock_verify:
            mock_verify.return_value = {
                "sdk_installed": True,
                "ndk_installed": True,
                "build_tools": ["33.0.0"],
                "platform_tools": True,
                "emulator": True,
                "system_images": [],
                "avds": [],
            }

            # Use typer's testing interface
            runner = CliRunner()

            runner.invoke(
                installer_cli.app,
                ["verify", "--verbose"],
            )

            # Verify verify_installation was called
            assert mock_verify.called

    def test_list_targets_command(self):
        """Test list-targets command."""
        # No need to mock anything - the command just displays static data
        runner = CliRunner()

        result = runner.invoke(
            installer_cli.app,
            ["list-targets"],
        )

        # Verify it ran without error
        assert result.exit_code == 0
        # Check that it displays something about API levels
        assert "API Level" in result.output
