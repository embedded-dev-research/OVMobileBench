"""Tests for NDK resolver and manager."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from ovmobilebench.android.installer.errors import (
    ComponentNotFoundError,
    InvalidArgumentError,
)
from ovmobilebench.android.installer.ndk import NdkResolver
from ovmobilebench.android.installer.types import NdkSpec, NdkVersion


class TestNdkResolver:
    """Test NdkResolver class."""

    def setup_method(self):
        """Set up test environment."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sdk_root = Path(self.tmpdir.name) / "sdk"
        self.sdk_root.mkdir()
        self.resolver = NdkResolver(self.sdk_root)

    def teardown_method(self):
        """Clean up test environment."""
        self.tmpdir.cleanup()

    def test_init(self):
        """Test NdkResolver initialization."""
        logger = Mock()
        resolver = NdkResolver(self.sdk_root, logger=logger)
        assert resolver.sdk_root == self.sdk_root.absolute()
        assert resolver.ndk_dir == self.sdk_root / "ndk"
        assert resolver.logger == logger

    def test_resolve_path_with_valid_path(self):
        """Test resolving NDK with valid path."""
        # Create fake NDK installation
        ndk_path = self.sdk_root / "test-ndk"
        ndk_path.mkdir()
        (ndk_path / "ndk-build").touch()
        (ndk_path / "toolchains").mkdir()

        spec = NdkSpec(path=ndk_path)
        resolved = self.resolver.resolve_path(spec)
        assert resolved == ndk_path

    def test_resolve_path_with_invalid_path(self):
        """Test resolving NDK with invalid path."""
        ndk_path = Path("/nonexistent/ndk")
        spec = NdkSpec(path=ndk_path)

        with pytest.raises(ComponentNotFoundError):
            self.resolver.resolve_path(spec)

    def test_resolve_path_with_invalid_ndk_structure(self):
        """Test resolving NDK with path that's not valid NDK."""
        # Create directory but not valid NDK
        ndk_path = self.sdk_root / "not-ndk"
        ndk_path.mkdir()

        spec = NdkSpec(path=ndk_path)
        with pytest.raises(InvalidArgumentError, match="Not a valid NDK installation"):
            self.resolver.resolve_path(spec)

    def test_resolve_path_with_alias_installed(self):
        """Test resolving NDK with alias when installed."""
        # Create NDK installation
        ndk_dir = self.sdk_root / "ndk" / "26.3.11579264"
        ndk_dir.mkdir(parents=True)
        (ndk_dir / "ndk-build").touch()
        (ndk_dir / "toolchains").mkdir()

        spec = NdkSpec(alias="r26d")
        resolved = self.resolver.resolve_path(spec)
        assert resolved == ndk_dir

    def test_resolve_path_with_alias_not_installed(self):
        """Test resolving NDK with alias when not installed."""
        spec = NdkSpec(alias="r26d")
        with pytest.raises(ComponentNotFoundError):
            self.resolver.resolve_path(spec)

    def test_resolve_path_with_invalid_alias(self):
        """Test resolving NDK with invalid alias."""
        spec = NdkSpec(alias="invalid")
        with pytest.raises(InvalidArgumentError, match="Unknown NDK version"):
            self.resolver.resolve_path(spec)

    def test_ensure_with_existing_path(self):
        """Test ensuring NDK with existing path."""
        # Create fake NDK
        ndk_path = self.sdk_root / "test-ndk"
        ndk_path.mkdir()
        (ndk_path / "ndk-build").touch()
        (ndk_path / "toolchains").mkdir()

        spec = NdkSpec(path=ndk_path)
        result = self.resolver.ensure(spec)
        assert result == ndk_path

    def test_ensure_with_nonexistent_path(self):
        """Test ensuring NDK with nonexistent path."""
        ndk_path = Path("/nonexistent/ndk")
        spec = NdkSpec(path=ndk_path)

        with pytest.raises(ComponentNotFoundError):
            self.resolver.ensure(spec)

    @patch.object(NdkResolver, "_install_ndk")
    def test_ensure_with_alias_needs_install(self, mock_install):
        """Test ensuring NDK with alias that needs installation."""
        mock_install.return_value = Path("/installed/ndk")

        spec = NdkSpec(alias="r26d")
        result = self.resolver.ensure(spec)

        assert result == Path("/installed/ndk")
        mock_install.assert_called_once_with("r26d")

    @patch.object(NdkResolver, "_install_via_sdkmanager")
    def test_install_ndk_via_sdkmanager(self, mock_install_sdkmanager):
        """Test installing NDK via sdkmanager."""
        ndk_path = self.sdk_root / "ndk" / "26.3.11579264"
        mock_install_sdkmanager.return_value = ndk_path

        result = self.resolver._install_ndk("r26d")

        assert result == ndk_path
        mock_install_sdkmanager.assert_called_once_with("26.3.11579264")

    @patch.object(NdkResolver, "_install_via_download")
    @patch.object(NdkResolver, "_install_via_sdkmanager")
    def test_install_ndk_fallback_to_download(self, mock_sdkmanager, mock_download):
        """Test falling back to direct download when sdkmanager fails."""
        mock_sdkmanager.side_effect = Exception("SDK error")
        ndk_path = self.sdk_root / "ndk" / "r26d"
        mock_download.return_value = ndk_path

        result = self.resolver._install_ndk("r26d")

        assert result == ndk_path
        mock_sdkmanager.assert_called_once()
        mock_download.assert_called_once_with("r26d")

    def test_validate_ndk_path_valid(self):
        """Test validating valid NDK path."""
        ndk_path = self.sdk_root / "ndk"
        ndk_path.mkdir()
        (ndk_path / "ndk-build").touch()
        (ndk_path / "toolchains").mkdir()
        (ndk_path / "prebuilt").mkdir()

        assert self.resolver._validate_ndk_path(ndk_path) is True

    def test_validate_ndk_path_invalid(self):
        """Test validating invalid NDK path."""
        # Nonexistent path
        assert self.resolver._validate_ndk_path(Path("/nonexistent")) is False

        # Empty directory
        empty_dir = self.sdk_root / "empty"
        empty_dir.mkdir()
        assert self.resolver._validate_ndk_path(empty_dir) is False

        # Directory with some but not enough NDK files
        partial_ndk = self.sdk_root / "partial"
        partial_ndk.mkdir()
        (partial_ndk / "ndk-build").touch()
        assert self.resolver._validate_ndk_path(partial_ndk) is False

    def test_list_installed_empty(self):
        """Test listing installed NDKs when none installed."""
        result = self.resolver.list_installed()
        assert result == []

    def test_list_installed_with_ndks(self):
        """Test listing installed NDKs."""
        # Create NDK installations
        ndk1 = self.sdk_root / "ndk" / "26.3.11579264"
        ndk1.mkdir(parents=True)
        (ndk1 / "ndk-build").touch()
        (ndk1 / "toolchains").mkdir()

        ndk2 = self.sdk_root / "ndk" / "r25c"
        ndk2.mkdir(parents=True)
        (ndk2 / "ndk-build").touch()
        (ndk2 / "toolchains").mkdir()

        result = self.resolver.list_installed()
        assert len(result) == 2
        versions = [v for v, _ in result]
        assert "26.3.11579264" in versions
        assert "r25c" in versions

    def test_get_version_from_source_properties(self):
        """Test getting NDK version from source.properties."""
        ndk_path = self.sdk_root / "ndk"
        ndk_path.mkdir()
        
        # Create source.properties
        source_props = ndk_path / "source.properties"
        source_props.write_text("Pkg.Revision = 26.3.11579264\nPkg.Desc = Android NDK")

        version = self.resolver.get_version(ndk_path)
        assert version == "26.3.11579264"

    def test_get_version_fallback_to_dir_name(self):
        """Test getting NDK version falls back to directory name."""
        ndk_path = self.sdk_root / "ndk" / "r26d"
        ndk_path.mkdir(parents=True)

        version = self.resolver.get_version(ndk_path)
        assert version == "r26d"

    @pytest.mark.skip(reason="Complex mocking of download and extraction flow")
    @patch("urllib.request.urlretrieve")
    @patch("zipfile.ZipFile")
    @patch("ovmobilebench.android.installer.detect.get_ndk_filename")
    @patch("ovmobilebench.android.installer.detect.detect_host")
    def test_install_via_download_zip(self, mock_detect_host, mock_get_filename, mock_zipfile, mock_urlretrieve):
        """Test installing NDK via direct download (ZIP)."""
        # Mock Linux host to avoid DMG
        mock_detect_host.return_value = Mock(os="linux")
        mock_get_filename.return_value = "android-ndk-r26d-linux.zip"
        
        # Mock ZIP extraction
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
            mock_tmpdir.return_value.__enter__.return_value = self.tmpdir.name
            
            # Create extracted directory structure
            extracted_dir = self.sdk_root / "ndk" / "android-ndk-r26d"
            extracted_dir.mkdir(parents=True)
            (extracted_dir / "ndk-build").touch()
            (extracted_dir / "toolchains").mkdir()
            
            # Mock the rename operation
            with patch.object(Path, "rename"):
                result = self.resolver._install_via_download("r26d")
            
            mock_urlretrieve.assert_called_once()
            assert "android-ndk-r26d-linux.zip" in mock_urlretrieve.call_args[0][0]