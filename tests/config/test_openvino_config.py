"""Tests for OpenVINOConfig schema."""

import pytest
from pydantic import ValidationError

from ovmobilebench.config.schema import BuildOptions, OpenVINOConfig, Toolchain


class TestOpenVINOConfig:
    """Test OpenVINOConfig validation and behavior."""

    def test_build_mode_valid(self):
        """Test valid build mode configuration."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            commit="HEAD",
            options=BuildOptions(CMAKE_BUILD_TYPE="Release"),
        )
        assert config.mode == "build"
        assert config.source_dir == "/path/to/openvino"
        assert config.commit == "HEAD"
        assert config.options.CMAKE_BUILD_TYPE == "Release"

    def test_build_mode_missing_source_dir(self):
        """Test build mode without source_dir - now allowed for auto-setup."""
        # This is now allowed - source_dir will be auto-configured
        config = OpenVINOConfig(mode="build")
        assert config.mode == "build"
        assert config.source_dir is None  # Will be auto-configured later

    def test_install_mode_valid(self):
        """Test valid install mode configuration."""
        config = OpenVINOConfig(mode="install", install_dir="/path/to/install")
        assert config.mode == "install"
        assert config.install_dir == "/path/to/install"

    def test_install_mode_missing_install_dir(self):
        """Test install mode without install_dir."""
        with pytest.raises(ValidationError, match="install_dir is required when mode is 'install'"):
            OpenVINOConfig(mode="install")

    def test_link_mode_valid(self):
        """Test valid link mode configuration."""
        config = OpenVINOConfig(mode="link", archive_url="http://example.com/openvino.tgz")
        assert config.mode == "link"
        assert config.archive_url == "http://example.com/openvino.tgz"

    def test_link_mode_latest(self):
        """Test link mode with 'latest' URL."""
        config = OpenVINOConfig(mode="link", archive_url="latest")
        assert config.mode == "link"
        assert config.archive_url == "latest"

    def test_link_mode_missing_archive_url(self):
        """Test link mode without archive_url."""
        with pytest.raises(ValidationError, match="archive_url is required when mode is 'link'"):
            OpenVINOConfig(mode="link")

    def test_invalid_mode(self):
        """Test invalid mode value."""
        with pytest.raises(ValidationError):
            OpenVINOConfig(mode="invalid", source_dir="/path")

    def test_build_mode_with_toolchain(self):
        """Test build mode with custom toolchain."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            toolchain=Toolchain(
                android_ndk="/path/to/ndk",
                abi="arm64-v8a",
                api_level=30,
            ),
        )
        assert config.toolchain.android_ndk == "/path/to/ndk"
        assert config.toolchain.abi == "arm64-v8a"
        assert config.toolchain.api_level == 30

    def test_build_mode_with_options(self):
        """Test build mode with custom build options."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(
                ENABLE_INTEL_GPU="ON",
                ENABLE_ONEDNN_FOR_ARM="ON",
                ENABLE_PYTHON="ON",
                BUILD_SHARED_LIBS="OFF",
            ),
        )
        assert config.options.ENABLE_INTEL_GPU == "ON"
        assert config.options.ENABLE_ONEDNN_FOR_ARM == "ON"
        assert config.options.ENABLE_PYTHON == "ON"
        assert config.options.BUILD_SHARED_LIBS == "OFF"

    def test_default_values(self):
        """Test default values for build mode."""
        config = OpenVINOConfig(mode="build", source_dir="/path/to/openvino")
        assert config.commit == "HEAD"
        assert config.options.CMAKE_BUILD_TYPE == "Release"  # Default from BuildOptions
        assert config.toolchain.abi == "arm64-v8a"
        assert config.toolchain.api_level == 24
        assert config.options.ENABLE_INTEL_GPU == "OFF"
        assert config.options.ENABLE_ONEDNN_FOR_ARM == "OFF"
        assert config.options.ENABLE_PYTHON == "OFF"
        assert config.options.BUILD_SHARED_LIBS == "ON"

    def test_build_types(self):
        """Test different build types."""
        for build_type in ["Release", "RelWithDebInfo", "Debug"]:
            config = OpenVINOConfig(
                mode="build",
                source_dir="/path/to/openvino",
                options=BuildOptions(CMAKE_BUILD_TYPE=build_type),
            )
            assert config.options.CMAKE_BUILD_TYPE == build_type

    def test_invalid_build_type(self):
        """Test invalid build type."""
        with pytest.raises(ValidationError):
            OpenVINOConfig(
                mode="build",
                source_dir="/path/to/openvino",
                options=BuildOptions(CMAKE_BUILD_TYPE="InvalidType"),
            )

    def test_mode_switching(self):
        """Test that different modes don't require other mode's fields."""
        # Build mode doesn't require install_dir or archive_url
        build_config = OpenVINOConfig(mode="build", source_dir="/path/to/source")
        assert build_config.install_dir is None
        assert build_config.archive_url is None

        # Install mode doesn't require source_dir or archive_url
        install_config = OpenVINOConfig(mode="install", install_dir="/path/to/install")
        assert install_config.source_dir is None
        assert install_config.archive_url is None

        # Link mode doesn't require source_dir or install_dir
        link_config = OpenVINOConfig(mode="link", archive_url="http://example.com/archive.tgz")
        assert link_config.source_dir is None
        assert link_config.install_dir is None
