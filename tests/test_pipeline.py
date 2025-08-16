"""Tests for Pipeline module."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from ovmobilebench.pipeline import Pipeline
from ovmobilebench.config.schema import Experiment
from ovmobilebench.core.errors import BuildError, DeviceError, RunError


class TestPipeline:
    """Test Pipeline class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock experiment config."""
        config = Mock(spec=Experiment)
        config.project.name = "test"
        config.project.run_id = "test-123"
        config.build.enabled = True
        config.device.type = "android"
        config.device.serial = "test_device"
        config.models = [Mock(name="model1", path="/path/to/model.xml")]
        config.run.repeats = 1
        config.run.matrix = {}
        config.report.sinks = []
        return config

    def test_init(self, mock_config):
        """Test Pipeline initialization."""
        with patch("ovmobilebench.pipeline.ArtifactManager") as mock_artifacts:
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config, verbose=True, dry_run=True)
                
                assert pipeline.config == mock_config
                assert pipeline.verbose is True
                assert pipeline.dry_run is True
                assert pipeline.artifacts is not None
                mock_artifacts.assert_called_once()

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    def test_build_enabled(self, mock_builder_class, mock_config):
        """Test build when enabled."""
        mock_config.build.enabled = True
        mock_builder = Mock()
        mock_builder_class.return_value = mock_builder
        
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                pipeline.build()
                
                mock_builder_class.assert_called_once()
                mock_builder.build.assert_called_once()

    def test_build_disabled(self, mock_config):
        """Test build when disabled."""
        mock_config.build.enabled = False
        
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                result = pipeline.build()
                
                assert result is None

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    def test_build_dry_run(self, mock_builder_class, mock_config):
        """Test build in dry run mode."""
        mock_config.build.enabled = True
        
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config, dry_run=True)
                pipeline.build()
                
                mock_builder_class.assert_not_called()

    @patch("ovmobilebench.pipeline.OpenVINOBuilder")
    def test_build_error(self, mock_builder_class, mock_config):
        """Test build error handling."""
        mock_config.build.enabled = True
        mock_builder = Mock()
        mock_builder.build.side_effect = BuildError("Build failed")
        mock_builder_class.return_value = mock_builder
        
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                
                with pytest.raises(BuildError):
                    pipeline.build()

    @patch("ovmobilebench.pipeline.Packager")
    def test_package(self, mock_packager_class, mock_config):
        """Test package."""
        mock_packager = Mock()
        mock_packager.create_bundle.return_value = Path("/bundle.tar.gz")
        mock_packager_class.return_value = mock_packager
        
        with patch("ovmobilebench.pipeline.ArtifactManager") as mock_artifacts:
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                pipeline.package()
                
                mock_packager_class.assert_called_once()
                mock_packager.create_bundle.assert_called_once()

    @patch("ovmobilebench.pipeline.Packager")
    def test_package_dry_run(self, mock_packager_class, mock_config):
        """Test package in dry run mode."""
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config, dry_run=True)
                pipeline.package()
                
                mock_packager_class.assert_not_called()

    @patch("ovmobilebench.pipeline.create_device")
    def test_deploy(self, mock_create_device, mock_config):
        """Test deploy."""
        mock_device = Mock()
        mock_create_device.return_value = mock_device
        
        with patch("ovmobilebench.pipeline.ArtifactManager") as mock_artifacts:
            mock_artifacts.return_value.get_bundle_path.return_value = Path("/bundle.tar.gz")
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                pipeline.deploy()
                
                mock_create_device.assert_called_once_with(mock_config.device)
                mock_device.push.assert_called()

    @patch("ovmobilebench.pipeline.create_device")
    def test_deploy_dry_run(self, mock_create_device, mock_config):
        """Test deploy in dry run mode."""
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config, dry_run=True)
                pipeline.deploy()
                
                mock_create_device.assert_not_called()

    @patch("ovmobilebench.pipeline.create_device")
    def test_deploy_error(self, mock_create_device, mock_config):
        """Test deploy error handling."""
        mock_device = Mock()
        mock_device.push.side_effect = DeviceError("Push failed")
        mock_create_device.return_value = mock_device
        
        with patch("ovmobilebench.pipeline.ArtifactManager") as mock_artifacts:
            mock_artifacts.return_value.get_bundle_path.return_value = Path("/bundle.tar.gz")
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                
                with pytest.raises(DeviceError):
                    pipeline.deploy()

    @patch("ovmobilebench.pipeline.BenchmarkRunner")
    @patch("ovmobilebench.pipeline.create_device")
    def test_run(self, mock_create_device, mock_runner_class, mock_config):
        """Test run."""
        mock_device = Mock()
        mock_create_device.return_value = mock_device
        mock_runner = Mock()
        mock_runner.run.return_value = [{"result": "data"}]
        mock_runner_class.return_value = mock_runner
        
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                pipeline.run()
                
                mock_runner_class.assert_called_once()
                mock_runner.run.assert_called_once()

    @patch("ovmobilebench.pipeline.BenchmarkRunner")
    @patch("ovmobilebench.pipeline.create_device")
    def test_run_dry_run(self, mock_create_device, mock_runner_class, mock_config):
        """Test run in dry run mode."""
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config, dry_run=True)
                pipeline.run()
                
                mock_runner_class.assert_not_called()

    @patch("ovmobilebench.pipeline.ReportGenerator")
    def test_report(self, mock_report_class, mock_config):
        """Test report generation."""
        mock_report = Mock()
        mock_report_class.return_value = mock_report
        
        with patch("ovmobilebench.pipeline.ArtifactManager") as mock_artifacts:
            mock_artifacts.return_value.get_results.return_value = [{"data": "test"}]
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                pipeline.report()
                
                mock_report_class.assert_called_once()
                mock_report.generate.assert_called_once()

    @patch("ovmobilebench.pipeline.ReportGenerator")
    def test_report_dry_run(self, mock_report_class, mock_config):
        """Test report in dry run mode."""
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config, dry_run=True)
                pipeline.report()
                
                mock_report_class.assert_not_called()

    def test_get_device(self, mock_config):
        """Test get_device method."""
        with patch("ovmobilebench.pipeline.create_device") as mock_create:
            mock_device = Mock()
            mock_create.return_value = mock_device
            
            with patch("ovmobilebench.pipeline.ArtifactManager"):
                with patch("ovmobilebench.pipeline.setup_logging"):
                    pipeline = Pipeline(mock_config)
                    
                    # First call creates device
                    device1 = pipeline._get_device()
                    assert device1 == mock_device
                    mock_create.assert_called_once()
                    
                    # Second call returns cached device
                    device2 = pipeline._get_device()
                    assert device2 == mock_device
                    mock_create.assert_called_once()  # Still only called once

    def test_cleanup(self, mock_config):
        """Test cleanup method."""
        with patch("ovmobilebench.pipeline.ArtifactManager"):
            with patch("ovmobilebench.pipeline.setup_logging"):
                pipeline = Pipeline(mock_config)
                
                # Set a device
                pipeline._device = Mock()
                
                # Cleanup should clear device
                pipeline._cleanup()
                assert pipeline._device is None