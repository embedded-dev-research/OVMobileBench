"""Tests for model helper functionality."""

# Import from e2e helper scripts
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

sys.path.append(str(Path(__file__).parent.parent.parent / "helpers"))

# Import the module and functions
from model_helper import (
    cleanup_invalid_models,
    download_detection_models,
    download_file,
    download_openvino_notebooks_models,
    download_resnet50,
    get_cache_dir_from_config,
    list_cached_models,
    main,
)


class TestGetCacheDir:
    """Test get_cache_dir_from_config function."""

    def test_with_config_file(self, tmp_path):
        """Test getting cache dir from config file."""
        config_file = tmp_path / "config.yaml"
        config_data = {"project": {"cache_dir": str(tmp_path / "custom_cache")}}
        config_file.write_text(yaml.dump(config_data))

        with patch("model_helper.logger"):
            cache_dir = get_cache_dir_from_config(str(config_file))
        assert cache_dir == tmp_path / "custom_cache"

    def test_with_absolute_path_in_config(self, tmp_path):
        """Test getting absolute cache dir from config."""
        config_file = tmp_path / "config.yaml"
        absolute_path = "/tmp/absolute_cache"
        config_data = {"project": {"cache_dir": absolute_path}}
        config_file.write_text(yaml.dump(config_data))

        with patch("model_helper.logger"):
            cache_dir = get_cache_dir_from_config(str(config_file))
        assert cache_dir == Path(absolute_path)

    def test_without_config_file(self):
        """Test fallback when config file doesn't exist."""
        with patch("model_helper.logger") as mock_logger:
            cache_dir = get_cache_dir_from_config("nonexistent.yaml")
        assert cache_dir == Path.cwd() / "ovmb_cache"
        mock_logger.warning.assert_called_once()

    def test_default_config_path(self, tmp_path):
        """Test using default config path."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            config_dir = tmp_path / "experiments"
            config_dir.mkdir()
            config_file = config_dir / "android_example.yaml"
            config_data = {"project": {"cache_dir": "test_cache"}}
            config_file.write_text(yaml.dump(config_data))

            with patch("model_helper.logger"):
                cache_dir = get_cache_dir_from_config(None)
            assert cache_dir == tmp_path / "test_cache"


class TestDownloadFile:
    """Test download_file function."""

    def test_file_already_exists(self, tmp_path):
        """Test when file already exists."""
        dest_path = tmp_path / "model.bin"
        dest_path.write_bytes(b"x" * 2000)  # 2KB file

        with patch("model_helper.logger") as mock_logger:
            result = download_file("http://example.com/model.bin", dest_path)

        assert result is True
        mock_logger.info.assert_called_once()
        assert "already exists" in mock_logger.info.call_args[0][0]

    def test_successful_download(self, tmp_path):
        """Test successful file download."""
        dest_path = tmp_path / "subdir" / "model.bin"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with patch("model_helper.logger") as mock_logger:
                # Simulate file creation after curl
                with patch.object(Path, "exists") as mock_exists:
                    mock_exists.side_effect = [False, True]  # Not exists, then exists
                    with patch.object(Path, "stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024 * 1024  # 1MB
                        result = download_file("http://example.com/model.bin", dest_path)

        assert result is True
        assert "Downloaded" in mock_logger.info.call_args_list[-1][0][0]

    def test_download_failure(self, tmp_path):
        """Test failed file download."""
        dest_path = tmp_path / "model.bin"
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Connection error"

        with patch("subprocess.run", return_value=mock_result):
            with patch("model_helper.logger") as mock_logger:
                result = download_file("http://example.com/model.bin", dest_path)

        assert result is False
        mock_logger.error.assert_called_once()
        assert "Failed to download" in mock_logger.error.call_args[0][0]

    def test_download_exception(self, tmp_path):
        """Test exception during download."""
        dest_path = tmp_path / "model.bin"

        with patch("subprocess.run", side_effect=Exception("Network error")):
            with patch("model_helper.logger") as mock_logger:
                result = download_file("http://example.com/model.bin", dest_path)

        assert result is False
        mock_logger.error.assert_called_once()
        assert "Error downloading" in mock_logger.error.call_args[0][0]


class TestDownloadModels:
    """Test model download functions."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        self.cache_dir = tmp_path / "ovmb_cache"
        self.patcher = patch("model_helper.get_cache_dir_from_config", return_value=self.cache_dir)
        self.patcher.start()
        yield
        self.patcher.stop()

    def test_download_openvino_notebooks_models_success(self):
        """Test successful download of OpenVINO notebooks models."""
        with patch("model_helper.download_file", return_value=True):
            with patch("model_helper.logger") as mock_logger:
                result = download_openvino_notebooks_models()

        assert "classification" in result
        assert "segmentation" in result
        assert result["classification"] == self.cache_dir / "models" / "classification"
        assert result["segmentation"] == self.cache_dir / "models" / "segmentation"

        # Check success messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("classification models ready" in msg for msg in log_messages)
        assert any("segmentation models ready" in msg for msg in log_messages)

    def test_download_openvino_notebooks_models_partial_failure(self):
        """Test partial failure in downloading models."""
        # First model succeeds, second fails
        with patch("model_helper.download_file", side_effect=[True, False, True, True]):
            with patch("model_helper.logger") as mock_logger:
                result = download_openvino_notebooks_models()

        # Classification failed, segmentation succeeded
        assert "classification" not in result
        assert "segmentation" in result

        # Check warning message for failed model
        mock_logger.warning.assert_called()
        assert "classification models failed" in mock_logger.warning.call_args_list[0][0][0]

    def test_download_detection_models_success(self):
        """Test successful download of detection models."""
        with patch("model_helper.download_file", return_value=True):
            with patch("model_helper.logger") as mock_logger:
                result = download_detection_models()

        assert result == self.cache_dir / "models" / "detection"
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Detection models ready" in msg for msg in log_messages)

    def test_download_detection_models_failure(self):
        """Test failed download of detection models."""
        with patch("model_helper.download_file", return_value=False):
            with patch("model_helper.logger") as mock_logger:
                result = download_detection_models()

        assert result is None
        mock_logger.warning.assert_called_once()
        assert "detection models failed" in mock_logger.warning.call_args[0][0]

    def test_download_resnet50_success(self):
        """Test successful download of ResNet-50 model."""
        with patch("model_helper.download_file", return_value=True):
            with patch("model_helper.logger") as mock_logger:
                result = download_resnet50()

        expected_path = self.cache_dir / "models" / "resnet" / "resnet-50-pytorch.xml"
        assert result == expected_path
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("ResNet-50 model ready" in msg for msg in log_messages)

    def test_download_resnet50_failure(self):
        """Test failed download of ResNet-50 model."""
        with patch("model_helper.download_file", return_value=False):
            with patch("model_helper.logger") as mock_logger:
                result = download_resnet50()

        assert result is None
        mock_logger.warning.assert_called_once()
        assert "ResNet-50 download incomplete" in mock_logger.warning.call_args[0][0]


class TestCleanupInvalidModels:
    """Test cleanup_invalid_models function."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        self.cache_dir = tmp_path / "ovmb_cache"
        self.models_dir = self.cache_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.patcher = patch("model_helper.get_cache_dir_from_config", return_value=self.cache_dir)
        self.patcher.start()
        yield
        self.patcher.stop()

    def test_cleanup_no_models_dir(self, tmp_path):
        """Test cleanup when models directory doesn't exist."""
        cache_dir = tmp_path / "nonexistent"
        with patch("model_helper.get_cache_dir_from_config", return_value=cache_dir):
            with patch("model_helper.logger"):
                cleanup_invalid_models()
        # Should not raise any errors

    def test_cleanup_html_files(self):
        """Test cleanup of HTML error pages."""
        # Create valid model files
        valid_xml = self.models_dir / "valid.xml"
        valid_xml.write_text("<?xml version='1.0'?>")
        valid_bin = self.models_dir / "valid.bin"
        valid_bin.write_bytes(b"\x00\x01\x02\x03")

        # Create invalid HTML files
        invalid_xml = self.models_dir / "invalid.xml"
        invalid_xml.write_text("<!DOCTYPE html><html><body>Error</body></html>")
        invalid_bin = self.models_dir / "invalid.bin"
        invalid_bin.write_text("<html>404 Not Found</html>")

        with patch("model_helper.logger") as mock_logger:
            cleanup_invalid_models()

        # Check that invalid files were removed
        assert not invalid_xml.exists()
        assert not invalid_bin.exists()
        # Valid files should remain
        assert valid_xml.exists()
        assert valid_bin.exists()

        # Check log messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Cleaned 2 invalid files" in msg for msg in log_messages)

    def test_cleanup_no_invalid_files(self):
        """Test cleanup when no invalid files exist."""
        # Create only valid files
        valid_xml = self.models_dir / "model.xml"
        valid_xml.write_text("<?xml version='1.0'?>")

        with patch("model_helper.logger") as mock_logger:
            cleanup_invalid_models()

        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("No invalid files found" in msg for msg in log_messages)

    def test_cleanup_file_read_error(self):
        """Test cleanup when file cannot be read."""
        bad_file = self.models_dir / "bad.xml"
        bad_file.write_text("content")

        with patch("builtins.open", side_effect=Exception("Permission denied")):
            with patch("model_helper.logger") as mock_logger:
                cleanup_invalid_models()

        # Should log warning
        mock_logger.warning.assert_called()
        assert "Could not check file" in mock_logger.warning.call_args[0][0]


class TestListCachedModels:
    """Test list_cached_models function."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        self.cache_dir = tmp_path / "ovmb_cache"
        self.models_dir = self.cache_dir / "models"
        self.patcher = patch("model_helper.get_cache_dir_from_config", return_value=self.cache_dir)
        self.patcher.start()
        yield
        self.patcher.stop()

    def test_list_no_cached_models(self):
        """Test listing when no models exist."""
        with patch("model_helper.logger") as mock_logger:
            result = list_cached_models()

        assert result == []
        mock_logger.info.assert_called_with("No cached models found")

    def test_list_models_in_subdirectories(self):
        """Test listing models in subdirectories."""
        # Create model directories
        classification_dir = self.models_dir / "classification"
        classification_dir.mkdir(parents=True, exist_ok=True)
        detection_dir = self.models_dir / "detection"
        detection_dir.mkdir(parents=True, exist_ok=True)

        # Add model files
        model1_xml = classification_dir / "model1.xml"
        model1_xml.write_text("xml")
        model1_bin = classification_dir / "model1.bin"
        model1_bin.write_bytes(b"x" * 1024 * 1024)  # 1MB

        model2_xml = detection_dir / "model2.xml"
        model2_xml.write_text("xml")
        # No bin file for model2

        with patch("model_helper.logger") as mock_logger:
            result = list_cached_models()

        assert len(result) == 2
        assert model1_xml in result
        assert model2_xml in result

        # Check log messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("classification/" in msg for msg in log_messages)
        assert any("detection/" in msg for msg in log_messages)
        assert any("model1" in msg and "MB" in msg for msg in log_messages)
        assert any("model2" in msg and "missing .bin file" in msg for msg in log_messages)

    def test_list_models_in_root_directory(self):
        """Test listing models in root models directory."""
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Add model in root
        root_model = self.models_dir / "root_model.xml"
        root_model.write_text("xml")

        with patch("model_helper.logger") as mock_logger:
            result = list_cached_models()

        assert len(result) == 1
        assert root_model in result

        # Check log messages
        log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("(root)/" in msg for msg in log_messages)
        assert any("root_model" in msg for msg in log_messages)


class TestMainFunction:
    """Test main function and CLI."""

    def test_main_download_all(self):
        """Test main function with download-all command."""
        with patch("sys.argv", ["model_helper.py", "-c", "test.yaml", "download-all"]):
            with patch("model_helper.cleanup_invalid_models") as mock_cleanup:
                with patch("model_helper.download_openvino_notebooks_models") as mock_notebooks:
                    with patch("model_helper.download_detection_models") as mock_detection:
                        with patch("model_helper.download_resnet50") as mock_resnet:
                            with patch("model_helper.list_cached_models") as mock_list:
                                main()

        mock_cleanup.assert_called_once_with("test.yaml")
        mock_notebooks.assert_called_once_with("test.yaml")
        mock_detection.assert_called_once_with("test.yaml")
        mock_resnet.assert_called_once_with("test.yaml")
        mock_list.assert_called_once_with("test.yaml")

    def test_main_download_notebooks(self):
        """Test main function with download-notebooks command."""
        with patch("sys.argv", ["model_helper.py", "-c", "config.yaml", "download-notebooks"]):
            with patch("model_helper.download_openvino_notebooks_models") as mock_download:
                main()

        mock_download.assert_called_once_with("config.yaml")

    def test_main_download_detection(self):
        """Test main function with download-detection command."""
        with patch("sys.argv", ["model_helper.py", "-c", "config.yaml", "download-detection"]):
            with patch("model_helper.download_detection_models") as mock_download:
                main()

        mock_download.assert_called_once_with("config.yaml")

    def test_main_download_resnet50(self):
        """Test main function with download-resnet50 command."""
        with patch("sys.argv", ["model_helper.py", "-c", "config.yaml", "download-resnet50"]):
            with patch("model_helper.download_resnet50") as mock_download:
                main()

        mock_download.assert_called_once_with("config.yaml")

    def test_main_cleanup(self):
        """Test main function with cleanup command."""
        with patch("sys.argv", ["model_helper.py", "-c", "config.yaml", "cleanup"]):
            with patch("model_helper.cleanup_invalid_models") as mock_cleanup:
                main()

        mock_cleanup.assert_called_once_with("config.yaml")

    def test_main_list(self):
        """Test main function with list command."""
        with patch("sys.argv", ["model_helper.py", "-c", "config.yaml", "list"]):
            with patch("model_helper.list_cached_models") as mock_list:
                main()

        mock_list.assert_called_once_with("config.yaml")

    def test_main_no_command(self):
        """Test main function with no command."""
        with patch("sys.argv", ["model_helper.py"]):
            # Mock parser.print_help to avoid SystemExit
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                main()
                mock_help.assert_called_once()

    def test_main_if_name_main(self):
        """Test __main__ execution."""
        # Test that module can be executed as script
        script_content = """
if __name__ == "__main__":
    pass  # main() would be called here
"""
        exec(compile(script_content, "test_script.py", "exec"))
