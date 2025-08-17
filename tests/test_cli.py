"""Tests for CLI module."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from ovmobilebench.cli import app

runner = CliRunner()


class TestCLI:
    """Test CLI commands."""

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_build_command(self, mock_pipeline_class, mock_load):
        """Test build command."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["build", "-c", "test.yaml"])

        assert result.exit_code == 0
        mock_load.assert_called_once()
        mock_pipeline_class.assert_called_once_with(mock_config, verbose=False, dry_run=False)
        mock_pipeline.build.assert_called_once()

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_build_command_verbose_dry_run(self, mock_pipeline_class, mock_load):
        """Test build command with verbose and dry run."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["build", "-c", "test.yaml", "-v", "--dry-run"])

        assert result.exit_code == 0
        mock_pipeline_class.assert_called_once_with(mock_config, verbose=True, dry_run=True)

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_package_command(self, mock_pipeline_class, mock_load):
        """Test package command."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["package", "-c", "test.yaml"])

        assert result.exit_code == 0
        mock_pipeline.package.assert_called_once()

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_deploy_command(self, mock_pipeline_class, mock_load):
        """Test deploy command."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["deploy", "-c", "test.yaml"])

        assert result.exit_code == 0
        mock_pipeline.deploy.assert_called_once()

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_run_command(self, mock_pipeline_class, mock_load):
        """Test run command."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["run", "-c", "test.yaml"])

        assert result.exit_code == 0
        mock_pipeline.run.assert_called_once()

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_report_command(self, mock_pipeline_class, mock_load):
        """Test report command."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["report", "-c", "test.yaml"])

        assert result.exit_code == 0
        mock_pipeline.report.assert_called_once()

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_all_command(self, mock_pipeline_class, mock_load):
        """Test all command."""
        mock_config = Mock()
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["all", "-c", "test.yaml"])

        assert result.exit_code == 0
        mock_pipeline.build.assert_called_once()
        mock_pipeline.package.assert_called_once()
        mock_pipeline.deploy.assert_called_once()
        mock_pipeline.run.assert_called_once()
        mock_pipeline.report.assert_called_once()

    @patch("ovmobilebench.cli.load_experiment")
    @patch("ovmobilebench.cli.Pipeline")
    def test_all_command_with_build_disabled(self, mock_pipeline_class, mock_load):
        """Test all command with build disabled in config."""
        mock_config = Mock()
        mock_config.build = Mock()
        mock_config.build.enabled = False
        mock_load.return_value = mock_config
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["all", "-c", "test.yaml"])

        assert result.exit_code == 0
        # Pipeline is created and methods are called
        mock_pipeline.build.assert_called_once()
        mock_pipeline.package.assert_called_once()

    @patch("ovmobilebench.devices.android.list_android_devices")
    def test_list_devices_command(self, mock_list):
        """Test list-devices command."""
        mock_list.return_value = ["device1", "device2"]

        result = runner.invoke(app, ["list-devices"])

        assert result.exit_code == 0
        mock_list.assert_called_once()
        assert "device1" in result.output
        assert "device2" in result.output

    @patch("ovmobilebench.devices.android.list_android_devices")
    def test_list_devices_empty(self, mock_list):
        """Test list-devices with no devices."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list-devices"])

        assert result.exit_code == 0
        assert "No Android devices found" in result.output

    @patch("ovmobilebench.devices.linux_ssh.list_ssh_devices")
    def test_list_ssh_devices_command(self, mock_list):
        """Test list-ssh-devices command."""
        mock_list.return_value = ["ssh_host1", "ssh_host2"]

        result = runner.invoke(app, ["list-ssh-devices"])

        assert result.exit_code == 0
        mock_list.assert_called_once()
        assert "ssh_host1" in result.output

    @patch("ovmobilebench.cli.list_ssh_devices")
    def test_list_ssh_devices_empty(self, mock_list):
        """Test list-ssh-devices with no devices."""
        mock_list.return_value = []

        result = runner.invoke(app, ["list-ssh-devices"])

        assert result.exit_code == 0
        assert "No SSH devices found" in result.output

    def test_help_command(self):
        """Test help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "End-to-end benchmarking pipeline" in result.output

    def test_version_callback(self):
        """Test version callback."""
        with patch("ovmobilebench.cli.typer") as mock_typer:
            from ovmobilebench.cli import version_callback

            mock_typer.Exit = Exception

            # Test when version is requested
            with pytest.raises(Exception):
                version_callback(True)

            # Test when version is not requested
            result = version_callback(False)
            assert result is None
