"""Android SDK/NDK installer module for OVMobileBench.

This module provides a comprehensive solution for installing and managing
Android SDK, NDK, and related tools across different platforms.

Example:
    >>> from ovmobilebench.android.installer import ensure_android_tools, NdkSpec
    >>> from pathlib import Path
    >>>
    >>> result = ensure_android_tools(
    ...     sdk_root=Path("/opt/android-sdk"),
    ...     api=30,
    ...     target="google_atd",
    ...     arch="arm64-v8a",
    ...     ndk=NdkSpec(alias="r26d")
    ... )
"""

from .api import (
    ensure_android_tools,
    export_android_env,
    verify_installation,
)
from .types import (
    Arch,
    InstallerResult,
    NdkSpec,
    Target,
)

__version__ = "0.1.0"

__all__ = [
    # Main functions
    "ensure_android_tools",
    "export_android_env",
    "verify_installation",
    # Types
    "Arch",
    "InstallerResult",
    "NdkSpec",
    "Target",
]
