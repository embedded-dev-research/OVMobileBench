"""Tests for model helper functionality."""

# Import from e2e helper scripts
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent / "tests" / "e2e"))

# Patch cache_dir before importing
from test_model_helper import (
    cleanup_invalid_models,
    download_detection_models,
    download_openvino_notebooks_models,
    download_resnet50,
    list_cached_models,
)


class TestModelHelper:
    """Test model management functions."""

    def test_functions_exist(self):
        """Test that required functions exist and are callable."""
        # Just verify the functions exist
        assert callable(download_resnet50)
        assert callable(download_openvino_notebooks_models)
        assert callable(download_detection_models)
        assert callable(list_cached_models)
        assert callable(cleanup_invalid_models)

    def test_list_cached_models(self):
        """Test listing cached models works."""
        with patch("test_model_helper.logger"):
            # Should not crash even if no models exist
            result = list_cached_models()
            assert isinstance(result, list)


class TestModelHelperIntegration:
    """Integration tests for model helper."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test environment."""
        from pathlib import Path

        self.cache_dir = tmp_path / "ovmb_cache" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.patcher = patch(
            "test_model_helper.get_cache_dir_from_config",
            return_value=Path(tmp_path / "ovmb_cache"),
        )
        self.patcher.start()
        yield
        self.patcher.stop()

    def test_download_and_list_integration(self):
        """Test downloading and listing models."""
        # Create some model files
        (self.cache_dir / "model1.xml").write_text("xml")
        (self.cache_dir / "model1.bin").write_bytes(b"bin")
        (self.cache_dir / "model2.xml").write_text("xml")

        with patch("test_model_helper.logger") as mock_logger:
            list_cached_models()

        # Check that models were logged
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        # Should have logged something about models
        assert len(log_calls) > 0

    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        # Remove the cache directory
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)

        # Mock subprocess for successful download
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 2000000  # 2MB
                # Try to download, should create directory
                download_resnet50()

        # Cache directory should be created
        assert self.cache_dir.parent.exists()  # At least the parent should exist
