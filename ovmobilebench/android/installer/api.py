"""Public API for Android installer module."""

from pathlib import Path
from typing import Dict, Optional

from .core import AndroidInstaller
from .env import export_android_env as _export_android_env
from .logging import get_logger
from .types import Arch, InstallerResult, NdkSpec, Target


def ensure_android_tools(
    *,
    sdk_root: Path,
    api: int,
    target: Target,
    arch: Arch,
    ndk: NdkSpec,
    install_platform_tools: bool = True,
    install_emulator: bool = True,
    install_build_tools: Optional[str] = None,
    create_avd_name: Optional[str] = None,
    accept_licenses: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
    jsonl_log: Optional[Path] = None,
) -> InstallerResult:
    """Ensure Android tools are installed.

    This is the main entry point for installing Android SDK, NDK, and related tools.

    Args:
        sdk_root: Root directory for Android SDK installation
        api: Android API level (e.g., 30 for Android 11)
        target: System image target (e.g., "google_atd", "google_apis")
        arch: Architecture (e.g., "arm64-v8a", "x86_64")
        ndk: NDK specification with alias or path
        install_platform_tools: Install platform-tools (adb, fastboot)
        install_emulator: Install emulator and system image
        install_build_tools: Optional build-tools version to install
        create_avd_name: Optional AVD name to create
        accept_licenses: Automatically accept SDK licenses
        dry_run: Only show what would be done without making changes
        verbose: Enable verbose logging
        jsonl_log: Optional path for JSON lines log file

    Returns:
        InstallerResult with installation details

    Raises:
        InvalidArgumentError: If arguments are invalid
        InstallerError: If installation fails

    Example:
        >>> from pathlib import Path
        >>> from ovmobilebench.android.installer.api import ensure_android_tools
        >>> from ovmobilebench.android.installer.types import NdkSpec
        >>>
        >>> result = ensure_android_tools(
        ...     sdk_root=Path("/opt/android-sdk"),
        ...     api=30,
        ...     target="google_atd",
        ...     arch="arm64-v8a",
        ...     ndk=NdkSpec(alias="r26d"),
        ...     create_avd_name="test_avd",
        ...     verbose=True
        ... )
        >>> print(f"SDK: {result['sdk_root']}")
        >>> print(f"NDK: {result['ndk_path']}")
    """
    # Create logger
    logger = get_logger(verbose=verbose, jsonl_path=jsonl_log)

    try:
        # Create installer
        installer = AndroidInstaller(sdk_root, logger=logger, verbose=verbose)

        # Run installation
        result = installer.ensure(
            api=api,
            target=target,
            arch=arch,
            ndk=ndk,
            install_platform_tools=install_platform_tools,
            install_emulator=install_emulator,
            install_build_tools=install_build_tools,
            create_avd_name=create_avd_name,
            accept_licenses=accept_licenses,
            dry_run=dry_run,
        )

        return result

    finally:
        # Close logger
        logger.close()


def export_android_env(
    *,
    github_env: Optional[Path] = None,
    print_stdout: bool = False,
    sdk_root: Path,
    ndk_path: Path,
) -> Dict[str, str]:
    """Export Android environment variables.

    Args:
        github_env: Path to GitHub environment file (for CI)
        print_stdout: Print export commands to stdout
        sdk_root: Android SDK root path
        ndk_path: Android NDK path

    Returns:
        Dictionary of exported environment variables

    Example:
        >>> from pathlib import Path
        >>> from ovmobilebench.android.installer.api import export_android_env
        >>>
        >>> env_vars = export_android_env(
        ...     sdk_root=Path("/opt/android-sdk"),
        ...     ndk_path=Path("/opt/android-sdk/ndk/26.1.10909125"),
        ...     print_stdout=True
        ... )
        export ANDROID_SDK_ROOT="/opt/android-sdk"
        export ANDROID_NDK="/opt/android-sdk/ndk/26.1.10909125"
    """
    return _export_android_env(
        github_env=github_env,
        print_stdout=print_stdout,
        sdk_root=sdk_root,
        ndk_path=ndk_path,
    )


def verify_installation(sdk_root: Path, verbose: bool = False) -> dict:
    """Verify Android tools installation.

    Args:
        sdk_root: Root directory for Android SDK
        verbose: Enable verbose logging

    Returns:
        Dictionary with verification results

    Example:
        >>> from pathlib import Path
        >>> from ovmobilebench.android.installer.api import verify_installation
        >>>
        >>> status = verify_installation(Path("/opt/android-sdk"))
        >>> print(f"Platform tools: {status['platform_tools']}")
        >>> print(f"NDK versions: {status.get('ndk_versions', [])}")
        >>> print(f"AVDs: {status.get('avds', [])}")
    """
    logger = get_logger(verbose=verbose) if verbose else None
    installer = AndroidInstaller(sdk_root, logger=logger, verbose=verbose)
    return installer.verify()


# Re-export commonly used types for convenience
__all__ = [
    "ensure_android_tools",
    "export_android_env",
    "verify_installation",
    "InstallerResult",
    "NdkSpec",
    "Target",
    "Arch",
]
