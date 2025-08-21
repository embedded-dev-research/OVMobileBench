"""Tests for model helper functionality."""

# Import from e2e helper scripts
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.append(str(Path(__file__).parent.parent.parent / "tests" / "e2e"))

from test_model_helper import (
    download_mobilenet,
    download_resnet50,
    list_cached_models,
)


class TestModelHelper:
    """Test model management functions."""

    def test_download_resnet50_new_download(self):
        """Test ResNet-50 download when files don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cache_dir = project_root / "ovmb_cache" / "models"

            # Mock the project root discovery
            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                # Mock requests
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {"content-length": "1000"}
                mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]

                with patch("requests.get", return_value=mock_response):
                    with patch("builtins.print"):  # Suppress progress output
                        result = download_resnet50()

                # Verify result
                expected_path = cache_dir / "resnet-50-pytorch.xml"
                assert result == expected_path

                # Verify cache directory was created
                assert cache_dir.exists()

                # Verify files were written
                xml_file = cache_dir / "resnet-50-pytorch.xml"
                bin_file = cache_dir / "resnet-50-pytorch.bin"
                assert xml_file.exists()
                assert bin_file.exists()

                # Verify content
                assert xml_file.read_bytes() == b"chunk1chunk2"
                assert bin_file.read_bytes() == b"chunk1chunk2"

    def test_download_resnet50_files_already_cached(self):
        """Test ResNet-50 download when files already exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cache_dir = project_root / "ovmb_cache" / "models"
            cache_dir.mkdir(parents=True)

            # Pre-create files
            xml_file = cache_dir / "resnet-50-pytorch.xml"
            bin_file = cache_dir / "resnet-50-pytorch.bin"
            xml_file.write_text("existing content")
            bin_file.write_text("existing content")

            # Mock the project root discovery
            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                with patch("requests.get") as mock_get:
                    result = download_resnet50()

                # Verify no network requests were made
                mock_get.assert_not_called()

                # Verify result
                assert result == xml_file

                # Verify files still exist with original content
                assert xml_file.read_text() == "existing content"

    def test_download_resnet50_network_error(self):
        """Test ResNet-50 download with network error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                with patch("requests.get") as mock_get:
                    mock_get.side_effect = requests.RequestException("Network error")

                    with pytest.raises(requests.RequestException):
                        download_resnet50()

    def test_download_resnet50_http_error(self):
        """Test ResNet-50 download with HTTP error response."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                mock_response = Mock()
                mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

                with patch("requests.get", return_value=mock_response):
                    with pytest.raises(requests.HTTPError):
                        download_resnet50()

    def test_download_resnet50_progress_display(self):
        """Test progress display during download."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {"content-length": "100"}
                mock_response.iter_content.return_value = [b"0" * 50, b"1" * 50]

                with patch("requests.get", return_value=mock_response):
                    with patch("builtins.print") as mock_print:
                        download_resnet50()

                        # Verify progress was displayed
                        progress_calls = [
                            call for call in mock_print.call_args_list if "Progress:" in str(call)
                        ]
                        assert len(progress_calls) > 0

    def test_download_resnet50_no_content_length(self):
        """Test download without content-length header."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {}  # No content-length
                mock_response.iter_content.return_value = [b"data"]

                with patch("requests.get", return_value=mock_response):
                    with patch("builtins.print"):
                        result = download_resnet50()

                        # Should still work without progress display
                        assert result is not None

    def test_download_mobilenet_not_implemented(self):
        """Test MobileNet download placeholder."""
        result = download_mobilenet()
        assert result is None

    def test_list_cached_models_no_cache_dir(self):
        """Test listing models when cache directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                models = list_cached_models()

                assert models == []

    def test_list_cached_models_empty_cache(self):
        """Test listing models with empty cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cache_dir = project_root / "ovmb_cache" / "models"
            cache_dir.mkdir(parents=True)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                models = list_cached_models()

                assert models == []

    def test_list_cached_models_with_models(self):
        """Test listing models with cached files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cache_dir = project_root / "ovmb_cache" / "models"
            cache_dir.mkdir(parents=True)

            # Create some model files
            model1 = cache_dir / "resnet50.xml"
            model2 = cache_dir / "mobilenet.xml"
            model3 = cache_dir / "other.bin"  # Should be ignored

            model1.touch()
            model2.touch()
            model3.touch()

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                models = list_cached_models()

                # Should only include .xml files
                assert len(models) == 2
                model_names = {model.name for model in models}
                assert model_names == {"resnet50.xml", "mobilenet.xml"}


class TestModelHelperCLI:
    """Test model helper CLI functionality."""

    def test_main_download_resnet50_command(self):
        """Test CLI download-resnet50 command."""
        with patch("test_model_helper.download_resnet50") as mock_download:
            with patch("sys.argv", ["test_model_helper.py", "download-resnet50"]):
                from test_model_helper import main

                main()

                mock_download.assert_called_once()

    def test_main_download_mobilenet_command(self):
        """Test CLI download-mobilenet command."""
        with patch("test_model_helper.download_mobilenet") as mock_download:
            with patch("sys.argv", ["test_model_helper.py", "download-mobilenet"]):
                from test_model_helper import main

                main()

                mock_download.assert_called_once()

    def test_main_list_command(self):
        """Test CLI list command."""
        with patch("test_model_helper.list_cached_models") as mock_list:
            with patch("sys.argv", ["test_model_helper.py", "list"]):
                from test_model_helper import main

                main()

                mock_list.assert_called_once()

    def test_main_no_command(self):
        """Test CLI with no command shows help."""
        with patch("sys.argv", ["test_model_helper.py"]):
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                from test_model_helper import main

                main()

                mock_help.assert_called_once()


class TestModelHelperIntegration:
    """Integration tests for model helper."""

    def test_download_and_list_integration(self):
        """Test complete download and list workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                # Mock successful download
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {"content-length": "1000"}
                mock_response.iter_content.return_value = [b"data"]

                with patch("requests.get", return_value=mock_response):
                    with patch("builtins.print"):
                        # Download model
                        download_result = download_resnet50()

                        # List models
                        models = list_cached_models()

                        # Verify integration
                        assert download_result in models
                        assert len(models) == 1  # Only XML files are counted by list_cached_models

    def test_cache_directory_creation(self):
        """Test that cache directory is created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            cache_dir = project_root / "ovmb_cache" / "models"

            # Ensure directory doesn't exist initially
            assert not cache_dir.exists()

            with patch("test_model_helper.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {"content-length": "100"}
                mock_response.iter_content.return_value = [b"data"]

                with patch("requests.get", return_value=mock_response):
                    with patch("builtins.print"):
                        download_resnet50()

                        # Verify directory was created
                        assert cache_dir.exists()
                        assert cache_dir.is_dir()
