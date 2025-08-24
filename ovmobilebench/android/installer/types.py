"""Type definitions for Android installer module."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

# Supported targets and architectures
Target = Literal["google_atd", "google_apis", "default", "aosp_atd"]
Arch = Literal["arm64-v8a", "x86_64", "x86", "armeabi-v7a"]


@dataclass(frozen=True)
class SystemImageSpec:
    """Specification for an Android system image."""

    api: int
    target: Target
    arch: Arch

    def to_package_id(self) -> str:
        """Convert to sdkmanager package ID."""
        return f"system-images;android-{self.api};{self.target};{self.arch}"


@dataclass(frozen=True)
class NdkSpec:
    """NDK specification with alias or path."""

    alias: str | None = None  # e.g. "r26d" or "26.1.10909125"
    path: Path | None = None  # absolute path overrides alias if provided

    def __post_init__(self):
        """Validate that at least one field is provided."""
        if not self.alias and not self.path:
            raise ValueError("Either alias or path must be provided for NDK")


@dataclass(frozen=True)
class InstallerPlan:
    """Installation plan detailing what needs to be installed."""

    need_cmdline_tools: bool
    need_platform_tools: bool
    need_platform: bool
    need_system_image: bool
    need_emulator: bool
    need_ndk: bool
    create_avd_name: str | None = None

    def has_work(self) -> bool:
        """Check if any installation is needed."""
        return any(
            [
                self.need_cmdline_tools,
                self.need_platform_tools,
                self.need_platform,
                self.need_system_image,
                self.need_emulator,
                self.need_ndk,
                self.create_avd_name,
            ]
        )


class InstallerResult(TypedDict):
    """Result of installation operation."""

    sdk_root: Path
    ndk_path: Path
    avd_created: bool
    performed: dict


@dataclass(frozen=True)
class AndroidVersion:
    """Android version information."""

    api_level: int
    version_name: str
    code_name: str

    @classmethod
    def from_api_level(cls, api: int) -> "AndroidVersion":
        """Get Android version info from API level."""
        versions = {
            35: ("15", "VanillaIceCream"),
            34: ("14", "UpsideDownCake"),
            33: ("13", "Tiramisu"),
            32: ("12L", "Sv2"),
            31: ("12", "S"),
            30: ("11", "R"),
            29: ("10", "Q"),
            28: ("9", "Pie"),
            27: ("8.1", "Oreo"),
            26: ("8.0", "Oreo"),
            25: ("7.1", "Nougat"),
            24: ("7.0", "Nougat"),
            23: ("6.0", "Marshmallow"),
            22: ("5.1", "Lollipop"),
            21: ("5.0", "Lollipop"),
        }
        if api not in versions:
            raise ValueError(f"Unknown API level: {api}")
        version_name, code_name = versions[api]
        return cls(api_level=api, version_name=version_name, code_name=code_name)


@dataclass(frozen=True)
class NdkVersion:
    """NDK version information."""

    alias: str  # e.g., "r26d"
    version: str  # e.g., "26.1.10909125"
    major: int  # e.g., 26
    minor: int  # e.g., 1
    patch: int  # e.g., 10909125

    @classmethod
    def from_alias(cls, alias: str) -> "NdkVersion":
        """Parse NDK version from alias like 'r26d'."""
        # Mapping of common NDK aliases to versions
        ndk_versions = {
            "r27c": "27.2.12479018",  # Latest LTS
            "r27b": "27.1.12297006",
            "r27": "27.0.11718014",
            "r26d": "26.3.11579264",
            "r26c": "26.2.11394342",
            "r26b": "26.1.10909125",
            "r26": "26.0.10792818",
            "r25c": "25.2.9519653",
            "r25b": "25.1.8937393",
            "r25": "25.0.8775105",
            "r24": "24.0.8215888",
            "r23c": "23.2.8568313",
            "r23b": "23.1.7779620",
            "r23": "23.0.7599858",
        }

        if alias not in ndk_versions:
            raise ValueError(f"Unknown NDK alias: {alias}")

        version = ndk_versions[alias]
        parts = version.split(".")
        return cls(
            alias=alias,
            version=version,
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2]),
        )

    @classmethod
    def from_version(cls, version: str) -> "NdkVersion":
        """Parse NDK version from version string like '26.1.10909125'."""
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid NDK version format: {version}")

        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])

        # Try to find the alias
        alias = f"r{major}"
        # Add letter suffix based on minor version
        if minor > 0:
            alias += chr(ord("a") + minor - 1)

        return cls(alias=alias, version=version, major=major, minor=minor, patch=patch)


@dataclass(frozen=True)
class HostInfo:
    """Host system information."""

    os: str  # "linux", "darwin", "windows"
    arch: str  # "x86_64", "arm64", etc.
    has_kvm: bool  # Linux KVM support
    java_version: str | None = None


@dataclass(frozen=True)
class SdkComponent:
    """SDK component information."""

    name: str
    package_id: str
    installed: bool
    version: str | None = None
    path: Path | None = None
