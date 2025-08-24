"""Tests for OpenVINO builder module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ovmobilebench.builders.openvino import OpenVINOBuilder
from ovmobilebench.config.schema import BuildOptions, OpenVINOConfig, Toolchain
from ovmobilebench.core.errors import BuildError


class TestOpenVINOBuilder:
    """Test OpenVINOBuilder class."""

    @pytest.fixture
    def build_config(self):
        """Create a test build configuration."""
        return OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            commit="HEAD",
            build_type="Release",
            toolchain=Toolchain(
                android_ndk="/path/to/ndk",
                abi="arm64-v8a",
                api_level=24,
                cmake="cmake",
                ninja="ninja",
            ),
            options=BuildOptions(
                ENABLE_INTEL_GPU="OFF",
                ENABLE_ONEDNN_FOR_ARM="OFF",
                ENABLE_PYTHON="OFF",
                BUILD_SHARED_LIBS="ON",
            ),
        )

    @pytest.fixture
    def install_config(self):
        """Create an install mode configuration."""
        return OpenVINOConfig(
            mode="install",
            install_dir="/path/to/openvino/install",
        )

    @pytest.fixture
    def build_config_no_ndk(self):
        """Create build config without Android NDK."""
        return OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            commit="HEAD",
            build_type="Release",
            toolchain=Toolchain(android_ndk=None),
        )

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_init(self, mock_ensure_dir, build_config):
        """Test OpenVINOBuilder initialization."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        assert builder.config == build_config
        assert builder.build_dir == Path("/build/dir")
        assert builder.verbose is False
        mock_ensure_dir.assert_called_once_with(Path("/build/dir"))

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_init_verbose(self, mock_ensure_dir, build_config):
        """Test OpenVINOBuilder initialization with verbose flag."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"), verbose=True)

        assert builder.verbose is True

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_build_wrong_mode(self, mock_ensure_dir, install_config):
        """Test build when using wrong mode."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(install_config, Path("/build/dir"))

        with pytest.raises(ValueError, match="OpenVINOBuilder can only be used with mode='build'"):
            builder.build()

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_build_enabled_success(self, mock_ensure_dir, build_config):
        """Test successful build when building is enabled."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with patch.object(builder, "_checkout_commit") as mock_checkout:
            with patch.object(builder, "_configure_cmake") as mock_configure:
                with patch.object(builder, "_build") as mock_build:
                    with patch("ovmobilebench.builders.openvino.logger") as mock_logger:
                        result = builder.build()

                        assert result == Path("/build/dir/bin")
                        mock_checkout.assert_called_once()
                        mock_configure.assert_called_once()
                        mock_build.assert_called_once()
                        mock_logger.info.assert_called_with(
                            "Building OpenVINO from /path/to/openvino"
                        )

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_checkout_commit_not_head(self, mock_run, mock_ensure_dir, build_config):
        """Test checking out specific commit."""
        mock_ensure_dir.return_value = Path("/build/dir")
        build_config.commit = "abc123"

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with patch("ovmobilebench.builders.openvino.logger") as mock_logger:
            builder._checkout_commit()

            mock_run.assert_called_once_with(
                "git checkout abc123",
                cwd=Path("/path/to/openvino"),
                check=True,
                verbose=False,
            )
            mock_logger.info.assert_called_once_with("Checked out commit: abc123")

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_checkout_commit_head(self, mock_run, mock_ensure_dir, build_config):
        """Test not checking out when commit is HEAD."""
        mock_ensure_dir.return_value = Path("/build/dir")
        # build_config.commit is "HEAD" by default

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))
        builder._checkout_commit()

        mock_run.assert_not_called()

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_configure_cmake_with_android_ndk(self, mock_run, mock_ensure_dir, build_config):
        """Test CMake configuration with Android NDK."""
        mock_ensure_dir.return_value = Path("/build/dir")
        mock_run.return_value = MagicMock(returncode=0)

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with patch("ovmobilebench.builders.openvino.logger"):
            builder._configure_cmake()

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]

            # Check key CMake arguments
            assert "cmake" in args
            assert "-S" in args
            assert "/path/to/openvino" in args
            assert "-B" in args
            # Check build dir argument - handle platform-specific path separators
            assert str(Path("/build/dir")) in args
            assert "-GNinja" in args
            assert "-DCMAKE_BUILD_TYPE=Release" in args
            assert "-DCMAKE_TOOLCHAIN_FILE=/path/to/ndk/build/cmake/android.toolchain.cmake" in args
            assert "-DANDROID_ABI=arm64-v8a" in args
            assert "-DANDROID_PLATFORM=android-24" in args
            assert "-DANDROID_STL=c++_shared" in args
            assert "-DENABLE_INTEL_GPU=OFF" in args
            assert "-DENABLE_ONEDNN_FOR_ARM=OFF" in args
            assert "-DENABLE_PYTHON=OFF" in args
            assert "-DBUILD_SHARED_LIBS=ON" in args
            assert "-DENABLE_TESTS=OFF" in args
            assert "-DENABLE_SAMPLES=ON" in args

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_configure_cmake_without_android_ndk(
        self, mock_run, mock_ensure_dir, build_config_no_ndk
    ):
        """Test CMake configuration without Android NDK."""
        mock_ensure_dir.return_value = Path("/build/dir")
        mock_run.return_value = MagicMock(returncode=0)

        builder = OpenVINOBuilder(build_config_no_ndk, Path("/build/dir"))

        with patch("ovmobilebench.builders.openvino.logger"):
            builder._configure_cmake()

            args = mock_run.call_args[0][0]

            # Android-specific args should not be present
            android_args = [
                arg for arg in args if "ANDROID" in arg or "android.toolchain.cmake" in arg
            ]
            assert len(android_args) == 0

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_configure_cmake_failure(self, mock_run, mock_ensure_dir, build_config):
        """Test CMake configuration failure."""
        mock_ensure_dir.return_value = Path("/build/dir")
        mock_run.return_value = MagicMock(returncode=1, stderr="CMake error")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with pytest.raises(BuildError) as exc_info:
            builder._configure_cmake()

        assert "CMake configuration failed: CMake error" in str(exc_info.value)

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_build_success(self, mock_run, mock_ensure_dir, build_config):
        """Test successful build."""
        mock_ensure_dir.return_value = Path("/build/dir")
        mock_run.return_value = MagicMock(returncode=0)

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with patch("ovmobilebench.builders.openvino.logger") as mock_logger:
            builder._build()

            # Should be called twice for two targets
            assert mock_run.call_count == 2

            # Check calls for both targets
            calls = mock_run.call_args_list
            # Use Path to handle platform-specific separators
            expected_path = str(Path("/build/dir"))
            assert calls[0][0][0] == ["ninja", "-C", expected_path, "benchmark_app"]
            assert calls[1][0][0] == ["ninja", "-C", expected_path, "openvino"]

            # Check logging
            log_calls = mock_logger.info.call_args_list
            assert any("Building target: benchmark_app" in str(call) for call in log_calls)
            assert any("Building target: openvino" in str(call) for call in log_calls)
            assert any("Build completed successfully" in str(call) for call in log_calls)

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_build_failure_first_target(self, mock_run, mock_ensure_dir, build_config):
        """Test build failure on first target."""
        mock_ensure_dir.return_value = Path("/build/dir")
        mock_run.return_value = MagicMock(returncode=1, stderr="Build error")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with pytest.raises(BuildError) as exc_info:
            builder._build()

        assert "Build failed for benchmark_app: Build error" in str(exc_info.value)
        # Should only be called once (fails on first target)
        assert mock_run.call_count == 1

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_build_failure_second_target(self, mock_run, mock_ensure_dir, build_config):
        """Test build failure on second target."""
        mock_ensure_dir.return_value = Path("/build/dir")
        # First call succeeds, second fails
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1, stderr="OpenVINO build error"),
        ]

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with pytest.raises(BuildError) as exc_info:
            builder._build()

        assert "Build failed for openvino: OpenVINO build error" in str(exc_info.value)
        # Should be called twice
        assert mock_run.call_count == 2

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_get_artifacts_success(self, mock_ensure_dir, build_config):
        """Test getting build artifacts when they exist."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        # Mock the artifact paths to exist
        with patch("pathlib.Path.exists", return_value=True):
            artifacts = builder.get_artifacts()

            expected = {
                "benchmark_app": Path("/build/dir/bin/aarch64/Release/benchmark_app"),
                "libs": Path("/build/dir/bin/aarch64/Release"),
            }
            assert artifacts == expected

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_get_artifacts_missing(self, mock_ensure_dir, build_config):
        """Test getting build artifacts when they don't exist."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        # Mock the artifact paths to not exist
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(BuildError) as exc_info:
                builder.get_artifacts()

            assert "Build artifact not found: benchmark_app" in str(exc_info.value)

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_get_artifacts_partially_missing(self, mock_ensure_dir, build_config):
        """Test getting build artifacts when some exist and some don't."""
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        # Mock benchmark_app exists but libs doesn't
        def mock_exists(path):
            return "benchmark_app" in str(path)

        with patch("pathlib.Path.exists", mock_exists):
            with pytest.raises(BuildError) as exc_info:
                builder.get_artifacts()

            assert "Build artifact not found: libs" in str(exc_info.value)

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    @patch("ovmobilebench.builders.openvino.run")
    def test_verbose_mode(self, mock_run, mock_ensure_dir, build_config):
        """Test that verbose mode is passed to run commands."""
        mock_ensure_dir.return_value = Path("/build/dir")
        mock_run.return_value = MagicMock(returncode=0)
        build_config.commit = "abc123"

        builder = OpenVINOBuilder(build_config, Path("/build/dir"), verbose=True)

        # Test checkout
        builder._checkout_commit()
        assert mock_run.call_args[1]["verbose"] is True

        # Test configure
        mock_run.reset_mock()
        builder._configure_cmake()
        assert mock_run.call_args[1]["verbose"] is True

        # Test build
        mock_run.reset_mock()
        builder._build()
        # Check both build calls have verbose=True
        for call in mock_run.call_args_list:
            assert call[1]["verbose"] is True

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_custom_build_type(self, mock_ensure_dir):
        """Test build with custom build type."""
        build_config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            build_type="Debug",
        )
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            builder._configure_cmake()

            args = mock_run.call_args[0][0]
            assert "-DCMAKE_BUILD_TYPE=Debug" in args

    @patch("ovmobilebench.builders.openvino.ensure_dir")
    def test_custom_toolchain_settings(self, mock_ensure_dir):
        """Test build with custom toolchain settings."""
        build_config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            toolchain=Toolchain(
                android_ndk="/custom/ndk",
                abi="x86_64",
                api_level=29,
            ),
        )
        mock_ensure_dir.return_value = Path("/build/dir")

        builder = OpenVINOBuilder(build_config, Path("/build/dir"))

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            builder._configure_cmake()

            args = mock_run.call_args[0][0]
            assert "-DCMAKE_TOOLCHAIN_FILE=/custom/ndk/build/cmake/android.toolchain.cmake" in args
            assert "-DANDROID_ABI=x86_64" in args
            assert "-DANDROID_PLATFORM=android-29" in args
