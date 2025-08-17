"""Custom exceptions for Android installer module."""

from pathlib import Path
from typing import Any


class InstallerError(Exception):
    """Base exception for all installer errors."""

    def __init__(self, message: str, details: dict | None = None):
        """Initialize with message and optional details."""
        super().__init__(message)
        self.details = details or {}


class InvalidArgumentError(InstallerError):
    """Invalid argument provided to installer."""

    def __init__(self, arg_name: str, value: Any, reason: str):
        """Initialize with argument details."""
        message = f"Invalid {arg_name}: {value} - {reason}"
        super().__init__(message, {"arg_name": arg_name, "value": value, "reason": reason})


class DownloadError(InstallerError):
    """Error downloading a component."""

    def __init__(self, url: str, reason: str, retry_hint: str | None = None):
        """Initialize with download details."""
        message = f"Failed to download from {url}: {reason}"
        if retry_hint:
            message += f"\nHint: {retry_hint}"
        super().__init__(message, {"url": url, "reason": reason, "retry_hint": retry_hint})


class UnpackError(InstallerError):
    """Error unpacking an archive."""

    def __init__(self, archive_path: Path, reason: str):
        """Initialize with archive details."""
        message = f"Failed to unpack {archive_path}: {reason}"
        super().__init__(message, {"archive_path": str(archive_path), "reason": reason})


class SdkManagerError(InstallerError):
    """Error running sdkmanager command."""

    def __init__(self, command: str, exit_code: int, stderr: str):
        """Initialize with command details."""
        message = f"sdkmanager failed with exit code {exit_code}: {stderr}"
        super().__init__(message, {"command": command, "exit_code": exit_code, "stderr": stderr})


class AvdManagerError(InstallerError):
    """Error managing AVDs."""

    def __init__(self, operation: str, avd_name: str, reason: str):
        """Initialize with AVD operation details."""
        message = f"AVD {operation} failed for '{avd_name}': {reason}"
        super().__init__(message, {"operation": operation, "avd_name": avd_name, "reason": reason})


class PermissionError(InstallerError):
    """Insufficient permissions for operation."""

    def __init__(self, path: Path, operation: str):
        """Initialize with permission details."""
        message = f"Permission denied for {operation} on {path}"
        super().__init__(message, {"path": str(path), "operation": operation})


class ComponentNotFoundError(InstallerError):
    """Required component not found."""

    def __init__(self, component: str, search_path: Path | None = None):
        """Initialize with component details."""
        message = f"Component '{component}' not found"
        if search_path:
            message += f" in {search_path}"
        super().__init__(
            message,
            {"component": component, "search_path": str(search_path) if search_path else None},
        )


class PlatformNotSupportedError(InstallerError):
    """Platform not supported for operation."""

    def __init__(self, platform: str, operation: str):
        """Initialize with platform details."""
        message = f"Platform '{platform}' not supported for {operation}"
        super().__init__(message, {"platform": platform, "operation": operation})


class DependencyError(InstallerError):
    """Missing or incompatible dependency."""

    def __init__(
        self,
        dependency: str,
        required_version: str | None = None,
        found_version: str | None = None,
    ):
        """Initialize with dependency details."""
        message = f"Dependency '{dependency}' "
        if required_version and found_version:
            message += f"version mismatch: required {required_version}, found {found_version}"
        elif required_version:
            message += f"version {required_version} required but not found"
        else:
            message += "not found"
        super().__init__(
            message,
            {
                "dependency": dependency,
                "required_version": required_version,
                "found_version": found_version,
            },
        )


class StateError(InstallerError):
    """Invalid state for operation."""

    def __init__(self, operation: str, current_state: str, required_state: str):
        """Initialize with state details."""
        message = f"Cannot {operation}: current state is '{current_state}', required state is '{required_state}'"
        super().__init__(
            message,
            {
                "operation": operation,
                "current_state": current_state,
                "required_state": required_state,
            },
        )


class NetworkError(InstallerError):
    """Network-related error."""

    def __init__(self, operation: str, reason: str, proxy_hint: bool = False):
        """Initialize with network error details."""
        message = f"Network error during {operation}: {reason}"
        if proxy_hint:
            message += "\nHint: Check proxy settings or network connectivity"
        super().__init__(
            message, {"operation": operation, "reason": reason, "proxy_hint": proxy_hint}
        )
