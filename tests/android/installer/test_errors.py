"""Tests for custom exceptions."""

from pathlib import Path

from ovmobilebench.android.installer.errors import (
    InstallerError,
    InvalidArgumentError,
    DownloadError,
    UnpackError,
    SdkManagerError,
    AvdManagerError,
    PermissionError as InstallerPermissionError,
    ComponentNotFoundError,
    PlatformNotSupportedError,
    DependencyError,
    StateError,
    NetworkError,
)


class TestInstallerError:
    """Test base InstallerError exception."""

    def test_creation_with_message(self):
        """Test creating InstallerError with message."""
        error = InstallerError("Test error message")
        assert str(error) == "Test error message"
        assert error.details == {}

    def test_creation_with_details(self):
        """Test creating InstallerError with details."""
        details = {"key": "value", "code": 42}
        error = InstallerError("Test error", details=details)
        assert str(error) == "Test error"
        assert error.details == details


class TestInvalidArgumentError:
    """Test InvalidArgumentError exception."""

    def test_creation(self):
        """Test creating InvalidArgumentError."""
        error = InvalidArgumentError("api", 99, "API level out of range")
        assert "Invalid api: 99 - API level out of range" in str(error)
        assert error.details["arg_name"] == "api"
        assert error.details["value"] == 99
        assert error.details["reason"] == "API level out of range"

    def test_inheritance(self):
        """Test that InvalidArgumentError inherits from InstallerError."""
        error = InvalidArgumentError("test", "value", "reason")
        assert isinstance(error, InstallerError)


class TestDownloadError:
    """Test DownloadError exception."""

    def test_creation_without_hint(self):
        """Test creating DownloadError without retry hint."""
        error = DownloadError("https://example.com/file.zip", "Connection timeout")
        assert "Failed to download from https://example.com/file.zip: Connection timeout" in str(
            error
        )
        assert error.details["url"] == "https://example.com/file.zip"
        assert error.details["reason"] == "Connection timeout"
        assert error.details["retry_hint"] is None

    def test_creation_with_hint(self):
        """Test creating DownloadError with retry hint."""
        error = DownloadError(
            "https://example.com/file.zip",
            "Connection timeout",
            retry_hint="Check network connectivity",
        )
        assert "Hint: Check network connectivity" in str(error)
        assert error.details["retry_hint"] == "Check network connectivity"


class TestUnpackError:
    """Test UnpackError exception."""

    def test_creation(self):
        """Test creating UnpackError."""
        archive_path = Path("/tmp/archive.zip")
        error = UnpackError(archive_path, "Corrupted archive")
        assert f"Failed to unpack {archive_path}: Corrupted archive" in str(error)
        assert error.details["archive_path"] == str(archive_path)
        assert error.details["reason"] == "Corrupted archive"


class TestSdkManagerError:
    """Test SdkManagerError exception."""

    def test_creation(self):
        """Test creating SdkManagerError."""
        error = SdkManagerError("sdkmanager --list", 1, "License not accepted")
        assert "sdkmanager failed with exit code 1: License not accepted" in str(error)
        assert error.details["command"] == "sdkmanager --list"
        assert error.details["exit_code"] == 1
        assert error.details["stderr"] == "License not accepted"


class TestAvdManagerError:
    """Test AvdManagerError exception."""

    def test_creation(self):
        """Test creating AvdManagerError."""
        error = AvdManagerError("create", "test_avd", "System image not found")
        assert "AVD create failed for 'test_avd': System image not found" in str(error)
        assert error.details["operation"] == "create"
        assert error.details["avd_name"] == "test_avd"
        assert error.details["reason"] == "System image not found"


class TestPermissionError:
    """Test PermissionError exception."""

    def test_creation(self):
        """Test creating PermissionError."""
        path = Path("/opt/android-sdk")
        error = InstallerPermissionError(path, "write")
        assert f"Permission denied for write on {path}" in str(error)
        assert error.details["path"] == str(path)
        assert error.details["operation"] == "write"


class TestComponentNotFoundError:
    """Test ComponentNotFoundError exception."""

    def test_creation_without_path(self):
        """Test creating ComponentNotFoundError without search path."""
        error = ComponentNotFoundError("platform-tools")
        assert "Component 'platform-tools' not found" in str(error)
        assert error.details["component"] == "platform-tools"
        assert error.details["search_path"] is None

    def test_creation_with_path(self):
        """Test creating ComponentNotFoundError with search path."""
        search_path = Path("/opt/android-sdk")
        error = ComponentNotFoundError("platform-tools", search_path)
        assert f"Component 'platform-tools' not found in {search_path}" in str(error)
        assert error.details["component"] == "platform-tools"
        assert error.details["search_path"] == str(search_path)


class TestPlatformNotSupportedError:
    """Test PlatformNotSupportedError exception."""

    def test_creation(self):
        """Test creating PlatformNotSupportedError."""
        error = PlatformNotSupportedError("freebsd", "NDK installation")
        assert "Platform 'freebsd' not supported for NDK installation" in str(error)
        assert error.details["platform"] == "freebsd"
        assert error.details["operation"] == "NDK installation"


class TestDependencyError:
    """Test DependencyError exception."""

    def test_creation_not_found(self):
        """Test creating DependencyError for not found dependency."""
        error = DependencyError("java")
        assert "Dependency 'java' not found" in str(error)
        assert error.details["dependency"] == "java"
        assert error.details["required_version"] is None
        assert error.details["found_version"] is None

    def test_creation_version_required(self):
        """Test creating DependencyError for required version."""
        error = DependencyError("java", required_version="17")
        assert "Dependency 'java' version 17 required but not found" in str(error)
        assert error.details["required_version"] == "17"

    def test_creation_version_mismatch(self):
        """Test creating DependencyError for version mismatch."""
        error = DependencyError("java", required_version="17", found_version="11")
        assert "Dependency 'java' version mismatch: required 17, found 11" in str(error)
        assert error.details["required_version"] == "17"
        assert error.details["found_version"] == "11"


class TestStateError:
    """Test StateError exception."""

    def test_creation(self):
        """Test creating StateError."""
        error = StateError("install NDK", "SDK not installed", "SDK installed")
        expected = "Cannot install NDK: current state is 'SDK not installed', required state is 'SDK installed'"
        assert expected in str(error)
        assert error.details["operation"] == "install NDK"
        assert error.details["current_state"] == "SDK not installed"
        assert error.details["required_state"] == "SDK installed"


class TestNetworkError:
    """Test NetworkError exception."""

    def test_creation_without_proxy_hint(self):
        """Test creating NetworkError without proxy hint."""
        error = NetworkError("download", "Connection refused")
        assert "Network error during download: Connection refused" in str(error)
        assert error.details["operation"] == "download"
        assert error.details["reason"] == "Connection refused"
        assert error.details["proxy_hint"] is False

    def test_creation_with_proxy_hint(self):
        """Test creating NetworkError with proxy hint."""
        error = NetworkError("download", "Connection refused", proxy_hint=True)
        assert "Hint: Check proxy settings or network connectivity" in str(error)
        assert error.details["proxy_hint"] is True
