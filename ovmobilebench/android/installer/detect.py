"""Host system detection utilities."""

import platform
import subprocess
from pathlib import Path
from typing import Optional

from .types import HostInfo


def detect_host() -> HostInfo:
    """Detect host system information.

    Returns:
        HostInfo with OS, architecture, and capabilities
    """
    os_name = platform.system().lower()
    arch = platform.machine().lower()

    # Normalize OS name
    if os_name == "darwin":
        os_name = "darwin"  # macOS
    elif os_name == "windows":
        os_name = "windows"
    else:
        os_name = "linux"  # Default to Linux for other Unix-like systems

    # Normalize architecture
    if arch in ["x86_64", "amd64"]:
        arch = "x86_64"
    elif arch in ["arm64", "aarch64"]:
        arch = "arm64"
    elif arch in ["i386", "i686"]:
        arch = "x86"
    elif arch in ["armv7l", "armv7"]:
        arch = "arm"

    # Check for KVM support (Linux only)
    has_kvm = False
    if os_name == "linux":
        has_kvm = Path("/dev/kvm").exists()

    # Try to detect Java version
    java_version = detect_java_version()

    return HostInfo(os=os_name, arch=arch, has_kvm=has_kvm, java_version=java_version)


def detect_java_version() -> Optional[str]:
    """Detect installed Java version.

    Returns:
        Java version string or None if not found
    """
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Java outputs version to stderr
        output = result.stderr
        if output:
            # Extract version from first line
            lines = output.strip().split("\n")
            if lines:
                # Parse version from string like:
                # openjdk version "17.0.8" 2023-07-18
                # java version "1.8.0_381"
                first_line = lines[0]
                if "version" in first_line:
                    parts = first_line.split('"')
                    if len(parts) >= 2:
                        return parts[1]
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    return None


def get_platform_suffix() -> str:
    """Get platform-specific file suffix for downloads.

    Returns:
        Platform suffix string (e.g., "linux", "darwin", "windows")
    """
    host = detect_host()
    return host.os


def get_sdk_tools_filename(version: str) -> str:
    """Get SDK command-line tools filename for current platform.

    Args:
        version: SDK tools version

    Returns:
        Filename for download
    """
    host = detect_host()
    platform_map = {
        "linux": "linux",
        "darwin": "mac",
        "windows": "win",
    }
    platform_name = platform_map.get(host.os, "linux")
    return f"commandlinetools-{platform_name}-{version}_latest.zip"


def get_ndk_filename(version: str) -> str:
    """Get NDK filename for current platform.

    Args:
        version: NDK version (e.g., "r26d")

    Returns:
        Filename for download
    """
    host = detect_host()
    if host.os == "windows":
        return f"android-ndk-{version}-windows.zip"
    elif host.os == "darwin":
        return f"android-ndk-{version}-darwin.dmg"
    else:
        return f"android-ndk-{version}-linux.zip"


def get_best_emulator_arch() -> str:
    """Get the best emulator architecture for current host.

    Returns:
        Recommended architecture for AVD
    """
    host = detect_host()

    # For ARM hosts, prefer ARM images
    if host.arch in ["arm64", "aarch64"]:
        return "arm64-v8a"
    elif host.arch in ["arm", "armv7l"]:
        return "armeabi-v7a"
    # For x86 hosts, prefer x86_64
    elif host.arch == "x86_64":
        # On Linux with KVM, ARM emulation is reasonably fast
        if host.os == "linux" and host.has_kvm:
            return "arm64-v8a"  # Can use ARM with KVM acceleration
        return "x86_64"
    else:
        return "x86"


def check_disk_space(path: Path, required_gb: float = 10.0) -> bool:
    """Check if there's enough disk space at path.

    Args:
        path: Path to check
        required_gb: Required space in GB

    Returns:
        True if enough space available
    """
    try:
        import shutil

        # Get disk usage statistics
        stat = shutil.disk_usage(path if path.exists() else path.parent)
        available_gb = stat.free / (1024**3)
        return available_gb >= required_gb
    except (OSError, AttributeError):
        # If we can't check, assume it's OK
        return True


def is_ci_environment() -> bool:
    """Check if running in CI environment.

    Returns:
        True if running in CI
    """
    import os

    ci_env_vars = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
        "AZURE_PIPELINES",
        "BITBUCKET_PIPELINES",
    ]
    return any(os.environ.get(var) for var in ci_env_vars)


def get_recommended_settings(host: Optional[HostInfo] = None) -> dict:
    """Get recommended installation settings for host.

    Args:
        host: Host info (will be detected if not provided)

    Returns:
        Dictionary with recommended settings
    """
    if host is None:
        host = detect_host()

    settings = {
        "api": 30,  # Default to API 30 (Android 11)
        "target": "google_atd",  # Automated Test Device for CI
        "arch": get_best_emulator_arch(),
        "ndk": "r26d",  # Stable NDK version
        "install_emulator": host.os != "windows",  # Skip emulator on Windows by default
        "create_avd": is_ci_environment(),  # Auto-create AVD in CI
    }

    # Adjust for CI environments
    if is_ci_environment():
        settings["target"] = "google_atd"  # Optimized for testing
        settings["install_emulator"] = True

    return settings