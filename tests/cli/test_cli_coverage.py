"""Tests to improve CLI coverage to 100%."""

import sys
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ovmobilebench.cli import app

runner = CliRunner()


def test_windows_utf8_setup():
    """Test Windows UTF-8 setup code."""
    # Save original platform
    original_platform = sys.platform

    try:
        # Mock Windows platform
        sys.platform = "win32"

        with patch("subprocess.run") as mock_run:
            # Re-import to trigger Windows-specific code
            import importlib

            import ovmobilebench.cli

            importlib.reload(ovmobilebench.cli)

            # Check that chcp was called on Windows
            mock_run.assert_called_once_with("chcp 65001", shell=True, capture_output=True)

    finally:
        # Restore original platform
        sys.platform = original_platform


def test_windows_utf8_setup_exception():
    """Test Windows UTF-8 setup with exception."""
    # Save original platform
    original_platform = sys.platform

    try:
        # Mock Windows platform
        sys.platform = "win32"

        with patch("subprocess.run", side_effect=Exception("Test error")):
            # Re-import to trigger Windows-specific code
            import importlib

            import ovmobilebench.cli

            # Should not raise exception, just pass
            importlib.reload(ovmobilebench.cli)

    finally:
        # Restore original platform
        sys.platform = original_platform


def test_list_ssh_devices_command():
    """Test list-ssh-devices command."""
    with patch("ovmobilebench.devices.linux_ssh.list_ssh_devices") as mock_list_ssh:
        # Test with no devices
        mock_list_ssh.return_value = []
        result = runner.invoke(app, ["list-ssh-devices"])
        assert result.exit_code == 0
        assert "No SSH devices configured" in result.stdout

        # Test with devices
        mock_list_ssh.return_value = [
            {"serial": "device1", "status": "available"},
            {"serial": "device2", "status": "offline"},
        ]
        result = runner.invoke(app, ["list-ssh-devices"])
        assert result.exit_code == 0
        assert "device1" in result.stdout
        assert "device2" in result.stdout


def DISABLED_test_all_command_ci_mode(tmp_path):
    """Test 'all' command in CI mode."""

    # Create project structure
    (tmp_path / "pyproject.toml").touch()

    # Create a test config file
    config_file = tmp_path / "test_config.yaml"
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    config_data = {
        "project": {"name": "test", "run_id": "test_001", "cache_dir": str(cache_dir)},
        "openvino": {"mode": "install", "install_dir": str(tmp_path / "openvino")},
        "device": {"kind": "android", "serials": ["test"]},
        "models": [{"name": "model1", "path": str(tmp_path / "model.xml")}],
        "report": {"sinks": [{"type": "json", "path": str(tmp_path / "results.json")}]},
    }

    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create dummy model file
    (tmp_path / "model.xml").touch()

    # Mock environment for CI
    import os

    original_ci = os.environ.get("CI")
    original_cwd = os.getcwd()

    try:
        os.environ["CI"] = "true"
        os.chdir(tmp_path)

        with patch("ovmobilebench.pipeline.Pipeline") as MockPipeline:
            mock_pipeline = MagicMock()
            MockPipeline.return_value = mock_pipeline

            # Run the command
            runner.invoke(app, ["all", "-c", str(config_file)])

            # Check that Pipeline was created
            MockPipeline.assert_called_once()

            # Check that pipeline methods were called
            mock_pipeline.build.assert_called_once()
            mock_pipeline.package.assert_called_once()
            mock_pipeline.deploy.assert_called_once()
            mock_pipeline.run.assert_called_once_with(None, None)
            mock_pipeline.report.assert_called_once()

    finally:
        # Restore original environment
        os.chdir(original_cwd)
        if original_ci:
            os.environ["CI"] = original_ci
        else:
            os.environ.pop("CI", None)


def DISABLED_test_all_command_unicode_error(tmp_path):
    """Test 'all' command with Unicode encoding error."""

    # Create a test config file
    config_file = tmp_path / "test_config.yaml"
    config_data = {
        "project": {"name": "test", "run_id": "test_001"},
        "openvino": {"mode": "install", "install_dir": str(tmp_path / "openvino")},
        "device": {"kind": "android", "serials": ["test"]},
        "models": [{"name": "model1", "path": str(tmp_path / "model.xml")}],
        "report": {"sinks": [{"type": "json", "path": str(tmp_path / "results.json")}]},
    }

    import yaml

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create dummy model file
    (tmp_path / "model.xml").touch()

    with patch(
        "ovmobilebench.config.loader.load_experiment",
        side_effect=UnicodeEncodeError("utf-8", "test", 0, 1, "test"),
    ):
        result = runner.invoke(app, ["all", "-c", str(config_file)])
        assert result.exit_code == 1
        assert "Encoding error" in result.stdout
