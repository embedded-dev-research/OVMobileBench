"""Tests for Pipeline OpenVINO modes (build, install, link)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from ovmobilebench.pipeline import Pipeline


class TestPipelineOpenVINOModes:
    """Test Pipeline OpenVINO modes functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create mock experiment config."""
        config = Mock()
        config.project = Mock()
        config.project.name = "test"
        config.project.run_id = "test-123"
        config.openvino = Mock()
        config.device = Mock()
        config.device.kind = "android"
        config.device.serials = ["test_device"]
        config.device.push_dir = "/data/local/tmp"
        config.package = Mock()
        config.run = Mock()
        config.run.warmup = False
        config.run.matrix = Mock()
        config.report = Mock()
        config.report.sinks = []
        config.report.aggregate = False
        config.report.tags = {}
        config.get_model_list = Mock(return_value=[])
        config.expand_matrix_for_model = Mock(return_value=[])
        return config

    def test_build_mode_install(self, mock_config):
        """Test build with install mode."""
        mock_config.openvino.mode = "install"
        mock_config.openvino.install_dir = "/path/to/install"

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)
            result = pipeline.build()

            assert result == Path("/path/to/install")

    def test_build_mode_install_no_dir(self, mock_config):
        """Test build with install mode but no install_dir."""
        mock_config.openvino.mode = "install"
        mock_config.openvino.install_dir = None

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            with pytest.raises(ValueError, match="install_dir must be specified"):
                pipeline.build()

    def test_build_mode_link(self, mock_config):
        """Test build with link mode."""
        mock_config.openvino.mode = "link"
        mock_config.openvino.archive_url = "http://example.com/openvino.tgz"

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")

            with patch.object(Pipeline, "_download_and_extract_openvino") as mock_download:
                mock_download.return_value = Path("/extracted/openvino")

                pipeline = Pipeline(mock_config)
                result = pipeline.build()

                assert result == Path("/extracted/openvino")
                mock_download.assert_called_once_with("http://example.com/openvino.tgz")

    def test_build_mode_link_no_url(self, mock_config):
        """Test build with link mode but no archive_url."""
        mock_config.openvino.mode = "link"
        mock_config.openvino.archive_url = None

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            with pytest.raises(ValueError, match="archive_url must be specified"):
                pipeline.build()

    def test_build_unknown_mode(self, mock_config):
        """Test build with unknown mode."""
        mock_config.openvino.mode = "unknown"

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            with pytest.raises(ValueError, match="Unknown OpenVINO mode: unknown"):
                pipeline.build()

    @patch("urllib.request.urlretrieve")
    @patch("tarfile.open")
    def test_download_and_extract_openvino(self, mock_tarfile, mock_urlretrieve, mock_config):
        """Test downloading and extracting OpenVINO archive."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            # Create a temp directory for testing

            with tempfile.TemporaryDirectory() as tmpdir:
                mock_ensure_dir.return_value = Path(tmpdir) / "test-123"
                pipeline = Pipeline(mock_config)

                # Setup tarfile mock
                mock_tar = MagicMock()
                mock_tarfile.return_value.__enter__.return_value = mock_tar

                # Mock Path methods
                with patch.object(Path, "glob") as mock_glob:
                    mock_glob.return_value = [Path(tmpdir) / "openvino" / "runtime"]

                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "exists", return_value=False):
                            pipeline._download_and_extract_openvino(
                                "http://example.com/openvino.tgz"
                            )

                            mock_urlretrieve.assert_called_once()
                            mock_tar.extractall.assert_called_once()

    @patch("urllib.request.urlopen")
    @patch("urllib.request.urlretrieve")
    @patch("tarfile.open")
    def test_download_and_extract_openvino_latest(
        self, mock_tarfile, mock_urlretrieve, mock_urlopen, mock_config
    ):
        """Test downloading latest OpenVINO archive."""
        # Mock the latest.json response
        latest_data = {
            "linux_aarch64": {"url": "http://example.com/linux_aarch64.tgz"},
            "ubuntu22_x86_64": {"url": "http://example.com/ubuntu22_x86_64.tgz"},
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(latest_data).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Setup tarfile mock
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:

            with tempfile.TemporaryDirectory() as tmpdir:
                mock_ensure_dir.return_value = Path(tmpdir) / "test-123"
                pipeline = Pipeline(mock_config)

                with patch.object(Path, "glob") as mock_glob:
                    mock_glob.return_value = [Path(tmpdir) / "openvino" / "runtime"]

                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "exists", return_value=False):
                            pipeline._download_and_extract_openvino("latest")

                            # For Android device, should select ARM64 build
                            mock_urlretrieve.assert_called_once()
                            args = mock_urlretrieve.call_args[0]
                            assert args[0] == "http://example.com/linux_aarch64.tgz"

    def test_download_and_extract_openvino_cached(self, mock_config):
        """Test using cached OpenVINO archive."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:

            with tempfile.TemporaryDirectory() as tmpdir:
                mock_ensure_dir.return_value = Path(tmpdir) / "test-123"
                pipeline = Pipeline(mock_config)

                with patch.object(Path, "glob") as mock_glob:
                    mock_glob.return_value = [Path(tmpdir) / "openvino" / "runtime"]

                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "exists", return_value=True):  # Files already exist
                            with patch("urllib.request.urlretrieve") as mock_urlretrieve:
                                pipeline._download_and_extract_openvino(
                                    "http://example.com/openvino.tgz"
                                )

                                # Should not download again
                                mock_urlretrieve.assert_not_called()

    def test_download_and_extract_openvino_no_dir_found(self, mock_config):
        """Test error when no OpenVINO directory found in archive."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:

            with tempfile.TemporaryDirectory() as tmpdir:
                mock_ensure_dir.return_value = Path(tmpdir) / "test-123"
                pipeline = Pipeline(mock_config)

                with patch("urllib.request.urlretrieve"):
                    with patch("tarfile.open"):
                        with patch.object(Path, "glob", return_value=[]):  # No directories found
                            with patch.object(Path, "exists", return_value=False):
                                with patch.object(
                                    Path, "iterdir", return_value=[Path("some_file.txt")]
                                ):
                                    with pytest.raises(
                                        ValueError,
                                        match="Could not find OpenVINO install directory",
                                    ):
                                        pipeline._download_and_extract_openvino(
                                            "http://example.com/openvino.tgz"
                                        )

    def test_get_install_artifacts(self, mock_config):
        """Test getting artifacts from install directory."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            install_dir = Path("/path/to/install")

            with patch.object(Path, "glob") as mock_glob:
                # Mock finding benchmark_app, lib, and plugins.xml
                def glob_side_effect(pattern):
                    if "benchmark_app" in pattern:
                        return [Path("/path/to/install/bin/benchmark_app")]
                    elif "lib" in pattern:
                        return [Path("/path/to/install/lib")]
                    elif "plugins.xml" in pattern:
                        return [Path("/path/to/install/plugins.xml")]
                    return []

                mock_glob.side_effect = glob_side_effect

                artifacts = pipeline._get_install_artifacts(install_dir)

                assert artifacts["benchmark_app"] == Path("/path/to/install/bin/benchmark_app")
                assert artifacts["lib_dir"] == Path("/path/to/install/lib")
                assert artifacts["plugins_xml"] == Path("/path/to/install/plugins.xml")

    def test_get_install_artifacts_empty(self, mock_config):
        """Test getting artifacts when none found."""
        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")
            pipeline = Pipeline(mock_config)

            install_dir = Path("/path/to/install")

            with patch.object(Path, "glob") as mock_glob:
                mock_glob.return_value = []

                artifacts = pipeline._get_install_artifacts(install_dir)

                assert artifacts == {}

    def test_package_install_mode(self, mock_config):
        """Test package creation with install mode."""
        mock_config.openvino.mode = "install"
        mock_config.openvino.install_dir = "/path/to/install"

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")

            with patch.object(Pipeline, "_get_install_artifacts") as mock_get_artifacts:
                mock_get_artifacts.return_value = {"benchmark_app": Path("/path/to/benchmark_app")}

                with patch("ovmobilebench.pipeline.Packager") as mock_packager_class:
                    mock_packager = Mock()
                    mock_packager.create_bundle.return_value = Path("/package.tar.gz")
                    mock_packager_class.return_value = mock_packager

                    pipeline = Pipeline(mock_config)
                    result = pipeline.package()

                    assert result == Path("/package.tar.gz")
                    mock_get_artifacts.assert_called_once_with(Path("/path/to/install"))

    def test_package_install_mode_no_dir(self, mock_config):
        """Test package creation with install mode but no install_dir."""
        mock_config.openvino.mode = "install"
        mock_config.openvino.install_dir = None

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")

            pipeline = Pipeline(mock_config)

            with pytest.raises(ValueError, match="install_dir must be specified"):
                pipeline.package()

    def test_package_link_mode(self, mock_config):
        """Test package creation with link mode."""
        mock_config.openvino.mode = "link"

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:
            mock_ensure_dir.return_value = Path("/artifacts/test-123")

            with patch.object(Pipeline, "_get_install_artifacts") as mock_get_artifacts:
                mock_get_artifacts.return_value = {"benchmark_app": Path("/path/to/benchmark_app")}

                with patch("ovmobilebench.pipeline.Packager") as mock_packager_class:
                    mock_packager = Mock()
                    mock_packager.create_bundle.return_value = Path("/package.tar.gz")
                    mock_packager_class.return_value = mock_packager

                    pipeline = Pipeline(mock_config)
                    result = pipeline.package()

                    assert result == Path("/package.tar.gz")
                    expected_dir = Path("/artifacts/test-123/openvino_download")
                    mock_get_artifacts.assert_called_once_with(expected_dir)

    @patch("platform.system")
    @patch("platform.machine")
    @patch("urllib.request.urlopen")
    @patch("urllib.request.urlretrieve")
    @patch("tarfile.open")
    def test_download_latest_linux_ssh(
        self, mock_tarfile, mock_urlretrieve, mock_urlopen, mock_machine, mock_system, mock_config
    ):
        """Test downloading latest for Linux SSH (Raspberry Pi)."""
        mock_config.device.kind = "linux_ssh"
        mock_system.return_value = "Linux"
        mock_machine.return_value = "aarch64"

        latest_data = {
            "rhel8_aarch64": {"url": "http://example.com/rhel8_aarch64.tgz"},
            "ubuntu22_x86_64": {"url": "http://example.com/ubuntu22_x86_64.tgz"},
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(latest_data).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Setup tarfile mock
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:

            with tempfile.TemporaryDirectory() as tmpdir:
                mock_ensure_dir.return_value = Path(tmpdir) / "test-123"
                pipeline = Pipeline(mock_config)

                with patch.object(Path, "glob") as mock_glob:
                    mock_glob.return_value = [Path(tmpdir) / "openvino" / "runtime"]

                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "exists", return_value=False):
                            pipeline._download_and_extract_openvino("latest")

                            # Should select ARM64 build for Raspberry Pi
                            args = mock_urlretrieve.call_args[0]
                            assert "aarch64" in args[0]

    @patch("platform.system")
    @patch("platform.machine")
    @patch("urllib.request.urlopen")
    @patch("urllib.request.urlretrieve")
    @patch("tarfile.open")
    def test_download_latest_macos(
        self, mock_tarfile, mock_urlretrieve, mock_urlopen, mock_machine, mock_system, mock_config
    ):
        """Test downloading latest for macOS."""
        mock_config.device.kind = "host"
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"

        latest_data = {
            "macos_arm64": {"url": "http://example.com/macos_arm64.tgz"},
            "ubuntu22_x86_64": {"url": "http://example.com/ubuntu22_x86_64.tgz"},
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(latest_data).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Setup tarfile mock
        mock_tar = MagicMock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar

        with patch("ovmobilebench.pipeline.ensure_dir") as mock_ensure_dir:

            with tempfile.TemporaryDirectory() as tmpdir:
                mock_ensure_dir.return_value = Path(tmpdir) / "test-123"
                pipeline = Pipeline(mock_config)

                with patch.object(Path, "glob") as mock_glob:
                    mock_glob.return_value = [Path(tmpdir) / "openvino" / "runtime"]

                    with patch.object(Path, "is_dir", return_value=True):
                        with patch.object(Path, "exists", return_value=False):
                            pipeline._download_and_extract_openvino("latest")

                            # Should select macOS build
                            args = mock_urlretrieve.call_args[0]
                            assert "macos" in args[0]
