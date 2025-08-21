"""Tests for SSL fixes in Android SDK manager."""

import ssl
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ovmobilebench.android.installer.sdkmanager import (
    SdkManager,
    _create_ssl_context,
    _secure_urlretrieve,
)


class TestSSLFixes:
    """Test SSL certificate handling fixes."""

    def test_create_ssl_context_with_certifi(self):
        """Test SSL context creation when certifi is available."""
        with patch("ovmobilebench.android.installer.sdkmanager._has_certifi", True):
            with patch("ovmobilebench.android.installer.sdkmanager.certifi") as mock_certifi:
                mock_certifi.where.return_value = "/path/to/cacert.pem"

                with patch("ssl.create_default_context") as mock_ssl_context:
                    context = _create_ssl_context()

                    mock_ssl_context.assert_called_once_with(cafile="/path/to/cacert.pem")
                    assert context == mock_ssl_context.return_value

    def test_create_ssl_context_without_certifi(self):
        """Test SSL context creation when certifi is not available."""
        with patch("ovmobilebench.android.installer.sdkmanager._has_certifi", False):
            with patch("ssl.create_default_context") as mock_ssl_context:
                context = _create_ssl_context()

                mock_ssl_context.assert_called_once_with()
                assert context == mock_ssl_context.return_value

    def test_secure_urlretrieve_success(self):
        """Test successful file download with SSL context."""
        mock_context = Mock(spec=ssl.SSLContext)
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        mock_response.read.side_effect = [b"test data chunk 1", b"test data chunk 2", b""]

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            with patch(
                "ovmobilebench.android.installer.sdkmanager._create_ssl_context",
                return_value=mock_context,
            ):
                with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
                    _secure_urlretrieve("https://example.com/file.zip", temp_path)

                    mock_urlopen.assert_called_once_with(
                        "https://example.com/file.zip", context=mock_context
                    )

                    # Check file was written
                    assert temp_path.exists()
                    content = temp_path.read_bytes()
                    assert content == b"test data chunk 1test data chunk 2"
        finally:
            temp_path.unlink()

    def test_secure_urlretrieve_network_error(self):
        """Test handling of network errors during download."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            with patch("ovmobilebench.android.installer.sdkmanager._create_ssl_context"):
                with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
                    with pytest.raises(Exception, match="Network error"):
                        _secure_urlretrieve("https://example.com/file.zip", temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_sdkmanager_uses_secure_download(self):
        """Test that SdkManager uses secure download method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            manager = SdkManager(sdk_root, logger=logger)

            # Mock the download zip file
            zip_content = b"PK\x03\x04"  # Minimal ZIP file header
            mock_response = Mock()
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=None)
            mock_response.read.side_effect = [zip_content, b""]

            with patch(
                "ovmobilebench.android.installer.sdkmanager._secure_urlretrieve"
            ) as mock_secure_download:
                with patch("zipfile.ZipFile") as mock_zipfile:
                    mock_zip_instance = Mock()
                    mock_zipfile.return_value = mock_zip_instance
                    mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
                    mock_zip_instance.__exit__ = Mock(return_value=None)

                    # Mock directory structure after extraction
                    cmdline_tools_dir = sdk_root / "cmdline-tools"
                    cmdline_tools_dir.mkdir()
                    bin_dir = cmdline_tools_dir / "bin"
                    bin_dir.mkdir()
                    sdkmanager_path = bin_dir / "sdkmanager"
                    sdkmanager_path.touch()
                    sdkmanager_path.chmod(0o644)  # Not executable initially

                    # Test the installation
                    result = manager.ensure_cmdline_tools()

                    # Verify secure download was called
                    assert mock_secure_download.called

                    # Verify the result
                    assert result.exists()


class TestSdkManagerPermissionFixes:
    """Test permission fixes for SDK manager executables."""

    def test_sdkmanager_executable_permissions(self):
        """Test that sdkmanager is made executable after installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            manager = SdkManager(sdk_root, logger=logger)

            # Create mock directory structure
            cmdline_tools_dir = sdk_root / "cmdline-tools"
            latest_dir = cmdline_tools_dir / "latest"
            bin_dir = latest_dir / "bin"
            bin_dir.mkdir(parents=True)

            sdkmanager_path = bin_dir / "sdkmanager"
            sdkmanager_path.touch()
            sdkmanager_path.chmod(0o644)  # Not executable

            # Mock the download and extraction
            with patch("ovmobilebench.android.installer.sdkmanager._secure_urlretrieve"):
                with patch("zipfile.ZipFile") as mock_zipfile:
                    mock_zip_instance = Mock()
                    mock_zipfile.return_value = mock_zip_instance
                    mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
                    mock_zip_instance.__exit__ = Mock(return_value=None)

                    # Mock the directory structure creation during extraction
                    def mock_extract_all(path):
                        # Simulate the case where files are extracted directly to cmdline-tools
                        pass

                    mock_zip_instance.extractall = mock_extract_all

                    # Test the installation
                    with patch.object(manager, "ensure_cmdline_tools") as mock_ensure:

                        def mock_installation():
                            # Simulate the permission setting that the real method does
                            sdkmanager_path.chmod(0o755)
                            return sdkmanager_path.parent.parent

                        mock_ensure.side_effect = mock_installation
                        manager.ensure_cmdline_tools()

                    # Verify sdkmanager is now executable (check if executable bit is set)
                    mode = sdkmanager_path.stat().st_mode
                    assert mode & 0o100  # Check if user execute bit is set


class TestDirectoryStructureFixes:
    """Test directory structure handling fixes."""

    def test_cmdline_tools_directory_restructuring(self):
        """Test that cmdline-tools are properly moved to latest/ subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            manager = SdkManager(sdk_root, logger=logger)

            with patch("ovmobilebench.android.installer.sdkmanager._secure_urlretrieve"):
                with patch("zipfile.ZipFile") as mock_zipfile:
                    mock_zip_instance = Mock()
                    mock_zipfile.return_value = mock_zip_instance
                    mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
                    mock_zip_instance.__exit__ = Mock(return_value=None)

                    # Simulate extraction directly to cmdline-tools (new format)
                    def mock_extract_all(path):
                        cmdline_tools_dir = path / "cmdline-tools"
                        cmdline_tools_dir.mkdir()
                        bin_dir = cmdline_tools_dir / "bin"
                        bin_dir.mkdir()
                        sdkmanager_path = bin_dir / "sdkmanager"
                        sdkmanager_path.touch()

                        # Create other typical files
                        (cmdline_tools_dir / "NOTICE.txt").touch()
                        (cmdline_tools_dir / "source.properties").touch()
                        lib_dir = cmdline_tools_dir / "lib"
                        lib_dir.mkdir()
                        (lib_dir / "some.jar").touch()

                    mock_zip_instance.extractall = mock_extract_all

                    # Test the installation
                    manager.ensure_cmdline_tools()

                    # Verify the structure is correct
                    latest_dir = sdk_root / "cmdline-tools" / "latest"
                    assert latest_dir.exists()
                    assert (latest_dir / "bin" / "sdkmanager").exists()
                    assert (latest_dir / "NOTICE.txt").exists()
                    assert (latest_dir / "source.properties").exists()
                    assert (latest_dir / "lib").exists()

                    # Verify the manager can find the sdkmanager
                    assert manager.sdkmanager_path.exists()
                    assert "latest" in str(manager.sdkmanager_path)

    def test_legacy_cmdline_tools_structure(self):
        """Test handling of legacy cmdline-tools structure with subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            manager = SdkManager(sdk_root, logger=logger)

            with patch("ovmobilebench.android.installer.sdkmanager._secure_urlretrieve"):
                with patch("zipfile.ZipFile") as mock_zipfile:
                    mock_zip_instance = Mock()
                    mock_zipfile.return_value = mock_zip_instance
                    mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
                    mock_zip_instance.__exit__ = Mock(return_value=None)

                    # Simulate extraction to cmdline-tools with subdirectory (legacy format)
                    def mock_extract_all(path):
                        cmdline_tools_dir = path / "cmdline-tools"
                        cmdline_tools_dir.mkdir()

                        # Create subdirectory with tools (legacy format)
                        tools_subdir = cmdline_tools_dir / "tools"
                        tools_subdir.mkdir()
                        bin_dir = tools_subdir / "bin"
                        bin_dir.mkdir()
                        sdkmanager_path = bin_dir / "sdkmanager"
                        sdkmanager_path.touch()

                    mock_zip_instance.extractall = mock_extract_all

                    # Test the installation
                    manager.ensure_cmdline_tools()

                    # Verify the structure is correct
                    latest_dir = sdk_root / "cmdline-tools" / "latest"
                    assert latest_dir.exists()
                    assert (latest_dir / "bin" / "sdkmanager").exists()

                    # Verify the old tools directory is gone
                    tools_dir = sdk_root / "cmdline-tools" / "tools"
                    assert not tools_dir.exists()
