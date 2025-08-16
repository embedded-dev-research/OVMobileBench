"""Tests for Pipeline module."""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from ovmobilebench.pipeline import Pipeline
from ovmobilebench.core.errors import BuildError, DeviceError


class TestPipeline:
    """Test Pipeline class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock experiment config."""
        config = Mock()
        config.project = Mock()
        config.project.name = "test"
        config.project.run_id = "test-123"
        config.build = Mock()
        config.build.enabled = True
        config.device = Mock()
        config.device.type = "android"
        config.device.serial = "test_device"
        config.models = [Mock(name="model1", path="/path/to/model.xml")]
        config.run = Mock()
        config.run.repeats = 1
        config.run.matrix = Mock()
        config.report = Mock()
        config.report.sinks = []
        return config

    def test_init(self, mock_config):
        """Test Pipeline initialization."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")

            pipeline = Pipeline(mock_config, verbose=True, dry_run=True)

            assert pipeline.config == mock_config
            assert pipeline.verbose is True
            assert pipeline.dry_run is True
            assert pipeline.artifacts_dir == Path("/artifacts/test-123")
            mock_ensure_dir.assert_called_once()

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    def test_build_enabled(self, mock_builder_class, mock_config):
        """Test build when enabled."""
        mock_config.build.enabled = True
        mock_builder = Mock()
        mock_builder.build.return_value = Path("/build/output")
        mock_builder_class.return_value = mock_builder

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            result = pipeline.build()

            assert result == Path("/build/output")
            mock_builder_class.assert_called_once()
            mock_builder.build.assert_called_once()

    def test_build_disabled(self, mock_config):
        """Test build when disabled."""
        mock_config.build.enabled = False

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            result = pipeline.build()

            assert result is None

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    def test_build_dry_run(self, mock_builder_class, mock_config):
        """Test build in dry run mode."""
        mock_config.build.enabled = True

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config, dry_run=True)
            result = pipeline.build()

            assert result is None
            mock_builder_class.assert_not_called()

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    def test_build_error(self, mock_builder_class, mock_config):
        """Test build error handling."""
        mock_config.build.enabled = True
        mock_builder = Mock()
        mock_builder.build.side_effect = BuildError("Build failed")
        mock_builder_class.return_value = mock_builder

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            with pytest.raises(BuildError):
                pipeline.build()

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    @patch("ovmobilebench.pipeline.Packager")
    def test_package(self, mock_packager_class, mock_builder_class, mock_config):
        """Test package."""
        mock_builder = Mock()
        mock_builder.get_artifacts.return_value = {"benchmark_app": Path("/bin/app")}
        mock_builder_class.return_value = mock_builder

        mock_packager = Mock()
        mock_packager.create_bundle.return_value = Path("/bundle.tar.gz")
        mock_packager_class.return_value = mock_packager

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            result = pipeline.package()

            assert result == Path("/bundle.tar.gz")
            mock_packager_class.assert_called_once()
            mock_packager.create_bundle.assert_called_once()

    @patch("ovmobilebench.pipeline.Packager")
    def test_package_dry_run(self, mock_packager_class, mock_config):
        """Test package in dry run mode."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config, dry_run=True)
            result = pipeline.package()

            assert result is None
            mock_packager_class.assert_not_called()

    def test_deploy(self, mock_config):
        """Test deploy."""
        mock_device = Mock()

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            pipeline.device = mock_device
            pipeline.package_path = Path("/bundle.tar.gz")

            pipeline.deploy()

            mock_device.push.assert_called_once()

    def test_deploy_dry_run(self, mock_config):
        """Test deploy in dry run mode."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config, dry_run=True)
            pipeline.package_path = Path("/bundle.tar.gz")

            pipeline.deploy()

            # Should not crash even without device

    def test_deploy_error(self, mock_config):
        """Test deploy error handling."""
        mock_device = Mock()
        mock_device.push.side_effect = DeviceError("Push failed")

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            pipeline.device = mock_device
            pipeline.package_path = Path("/bundle.tar.gz")

            with pytest.raises(DeviceError):
                pipeline.deploy()

    @patch("ovmobilebench.pipeline.BenchmarkRunner")
    def test_run(self, mock_runner_class, mock_config):
        """Test run."""
        mock_runner = Mock()
        mock_runner.run_matrix.return_value = [{"result": "data"}]
        mock_runner_class.return_value = mock_runner

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            pipeline.device = Mock()

            pipeline.run()

            mock_runner_class.assert_called_once()
            mock_runner.run_matrix.assert_called_once()
            assert pipeline.results == [{"result": "data"}]

    @patch("ovmobilebench.pipeline.BenchmarkRunner")
    def test_run_dry_run(self, mock_runner_class, mock_config):
        """Test run in dry run mode."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config, dry_run=True)

            pipeline.run()

            mock_runner_class.assert_not_called()

    @patch("ovmobilebench.pipeline.BenchmarkParser")
    @patch("ovmobilebench.pipeline.JSONSink")
    def test_report(self, mock_json_sink_class, mock_parser_class, mock_config):
        """Test report generation."""
        mock_config.report.sinks = ["json"]
        mock_config.report.aggregate = False
        mock_config.report.tags = {}

        mock_parser = Mock()
        mock_parser.parse_result.return_value = {"parsed": "data"}
        mock_parser_class.return_value = mock_parser

        mock_sink = Mock()
        mock_json_sink_class.return_value = mock_sink

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            pipeline.results = [{"raw": "result"}]

            pipeline.report()

            mock_parser.parse_result.assert_called_once()
            mock_sink.write.assert_called_once()

    def test_report_dry_run(self, mock_config):
        """Test report in dry run mode."""
        mock_config.report.aggregate = False
        mock_config.report.tags = {}
        mock_config.report.sinks = []

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config, dry_run=True)
            pipeline.results = [{"raw": "result"}]

            # Dry run should still process results but not write
            pipeline.report()

            # Should not crash

    @patch("ovmobilebench.pipeline.AndroidDevice")
    def test_get_device_android(self, mock_android_class, mock_config):
        """Test getting Android device using _get_device."""
        mock_config.device.kind = "android"  # Use 'kind' not 'type' for android
        mock_config.device.serial = "test_device"
        mock_config.device.push_dir = "/data/local/tmp"
        mock_device = Mock()
        mock_android_class.return_value = mock_device

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            # _get_device is a private method
            device = pipeline._get_device(mock_config.device.serial)

            assert device == mock_device
            mock_android_class.assert_called_once_with(
                mock_config.device.serial, mock_config.device.push_dir
            )

    def test_prepare_device(self, mock_config):
        """Test _prepare_device method."""
        mock_device = Mock()

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            pipeline._prepare_device(mock_device)

            # Check that device preparation methods are called
            mock_device.disable_animations.assert_called_once()
            mock_device.screen_off.assert_called_once()
