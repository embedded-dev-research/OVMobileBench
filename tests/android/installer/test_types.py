"""Tests for type definitions."""

import pytest
from pathlib import Path

from ovmobilebench.android.installer.types import (
    AndroidVersion,
    NdkSpec,
    NdkVersion,
    SystemImageSpec,
    InstallerPlan,
    SdkComponent,
    HostInfo,
)


class TestSystemImageSpec:
    """Test SystemImageSpec data model."""

    def test_creation(self):
        """Test creating SystemImageSpec."""
        spec = SystemImageSpec(api=30, target="google_atd", arch="arm64-v8a")
        assert spec.api == 30
        assert spec.target == "google_atd"
        assert spec.arch == "arm64-v8a"

    def test_to_package_id(self):
        """Test converting to package ID."""
        spec = SystemImageSpec(api=30, target="google_atd", arch="arm64-v8a")
        assert spec.to_package_id() == "system-images;android-30;google_atd;arm64-v8a"

    def test_immutable(self):
        """Test that SystemImageSpec is immutable."""
        spec = SystemImageSpec(api=30, target="google_atd", arch="arm64-v8a")
        with pytest.raises(AttributeError):
            spec.api = 31


class TestNdkSpec:
    """Test NdkSpec data model."""

    def test_creation_with_alias(self):
        """Test creating NdkSpec with alias."""
        spec = NdkSpec(alias="r26d")
        assert spec.alias == "r26d"
        assert spec.path is None

    def test_creation_with_path(self):
        """Test creating NdkSpec with path."""
        path = Path("/opt/android-ndk")
        spec = NdkSpec(path=path)
        assert spec.path == path
        assert spec.alias is None

    def test_creation_with_both(self):
        """Test creating NdkSpec with both alias and path."""
        path = Path("/opt/android-ndk")
        spec = NdkSpec(alias="r26d", path=path)
        assert spec.alias == "r26d"
        assert spec.path == path

    def test_creation_without_both_fails(self):
        """Test that creating NdkSpec without alias or path fails."""
        with pytest.raises(ValueError, match="Either alias or path must be provided"):
            NdkSpec()


class TestAndroidVersion:
    """Test AndroidVersion data model."""

    def test_from_api_level_valid(self):
        """Test creating AndroidVersion from valid API level."""
        version = AndroidVersion.from_api_level(30)
        assert version.api_level == 30
        assert version.version_name == "11"
        assert version.code_name == "R"

    def test_from_api_level_invalid(self):
        """Test creating AndroidVersion from invalid API level."""
        with pytest.raises(ValueError, match="Unknown API level"):
            AndroidVersion.from_api_level(99)

    def test_known_versions(self):
        """Test some known Android versions."""
        test_cases = [
            (21, "5.0", "Lollipop"),
            (23, "6.0", "Marshmallow"),
            (28, "9", "Pie"),
            (30, "11", "R"),
            (33, "13", "Tiramisu"),
            (34, "14", "UpsideDownCake"),
        ]
        for api, version_name, code_name in test_cases:
            version = AndroidVersion.from_api_level(api)
            assert version.api_level == api
            assert version.version_name == version_name
            assert version.code_name == code_name


class TestNdkVersion:
    """Test NdkVersion data model."""

    def test_from_alias_valid(self):
        """Test creating NdkVersion from valid alias."""
        version = NdkVersion.from_alias("r26d")
        assert version.alias == "r26d"
        assert version.version == "26.3.11579264"
        assert version.major == 26
        assert version.minor == 3
        assert version.patch == 11579264

    def test_from_alias_invalid(self):
        """Test creating NdkVersion from invalid alias."""
        with pytest.raises(ValueError, match="Unknown NDK alias"):
            NdkVersion.from_alias("r99z")

    def test_from_version_valid(self):
        """Test creating NdkVersion from version string."""
        version = NdkVersion.from_version("26.1.10909125")
        assert version.version == "26.1.10909125"
        assert version.major == 26
        assert version.minor == 1
        assert version.patch == 10909125
        assert version.alias == "r26a"  # Minor version 1 = 'a'

    def test_from_version_invalid(self):
        """Test creating NdkVersion from invalid version string."""
        with pytest.raises(ValueError, match="Invalid NDK version format"):
            NdkVersion.from_version("26.1")

    def test_known_ndk_versions(self):
        """Test some known NDK versions."""
        known_versions = {
            "r26d": "26.3.11579264",
            "r26c": "26.2.11394342",
            "r25c": "25.2.9519653",
            "r24": "24.0.8215888",
        }
        for alias, expected_version in known_versions.items():
            version = NdkVersion.from_alias(alias)
            assert version.alias == alias
            assert version.version == expected_version


class TestInstallerPlan:
    """Test InstallerPlan data model."""

    def test_creation(self):
        """Test creating InstallerPlan."""
        plan = InstallerPlan(
            need_cmdline_tools=True,
            need_platform_tools=True,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=True,
            create_avd_name="test_avd",
        )
        assert plan.need_cmdline_tools is True
        assert plan.need_platform_tools is True
        assert plan.need_platform is False
        assert plan.need_ndk is True
        assert plan.create_avd_name == "test_avd"

    def test_has_work_true(self):
        """Test has_work returns True when work needed."""
        plan = InstallerPlan(
            need_cmdline_tools=False,
            need_platform_tools=True,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=False,
        )
        assert plan.has_work() is True

    def test_has_work_false(self):
        """Test has_work returns False when no work needed."""
        plan = InstallerPlan(
            need_cmdline_tools=False,
            need_platform_tools=False,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=False,
            create_avd_name=None,
        )
        assert plan.has_work() is False

    def test_has_work_with_avd(self):
        """Test has_work returns True when AVD creation needed."""
        plan = InstallerPlan(
            need_cmdline_tools=False,
            need_platform_tools=False,
            need_platform=False,
            need_system_image=False,
            need_emulator=False,
            need_ndk=False,
            create_avd_name="test_avd",
        )
        assert plan.has_work() is True


class TestHostInfo:
    """Test HostInfo data model."""

    def test_creation(self):
        """Test creating HostInfo."""
        host = HostInfo(
            os="linux",
            arch="x86_64",
            has_kvm=True,
            java_version="17.0.8",
        )
        assert host.os == "linux"
        assert host.arch == "x86_64"
        assert host.has_kvm is True
        assert host.java_version == "17.0.8"

    def test_creation_without_java(self):
        """Test creating HostInfo without Java version."""
        host = HostInfo(os="darwin", arch="arm64", has_kvm=False)
        assert host.os == "darwin"
        assert host.arch == "arm64"
        assert host.has_kvm is False
        assert host.java_version is None


class TestSdkComponent:
    """Test SdkComponent data model."""

    def test_creation_installed(self):
        """Test creating installed SdkComponent."""
        component = SdkComponent(
            name="Platform Tools",
            package_id="platform-tools",
            installed=True,
            version="34.0.5",
            path=Path("/opt/sdk/platform-tools"),
        )
        assert component.name == "Platform Tools"
        assert component.package_id == "platform-tools"
        assert component.installed is True
        assert component.version == "34.0.5"
        assert component.path == Path("/opt/sdk/platform-tools")

    def test_creation_not_installed(self):
        """Test creating not installed SdkComponent."""
        component = SdkComponent(
            name="Emulator",
            package_id="emulator",
            installed=False,
        )
        assert component.name == "Emulator"
        assert component.package_id == "emulator"
        assert component.installed is False
        assert component.version is None
        assert component.path is None
