"""Tests for CMake installation in Android SDK."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from ovmobilebench.android.installer.core import AndroidInstaller
from ovmobilebench.android.installer.sdkmanager import SdkManager


class TestCMakeInstallation:
    """Test CMake installation functionality."""

    def test_ensure_cmake_not_installed(self):
        """Test CMake installation when not present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            manager = SdkManager(sdk_root, logger=logger)

            # Mock sdkmanager execution
            with patch.object(manager, "_run_sdkmanager") as mock_run:
                # Create cmake directory after "installation"
                def create_cmake_dir(args):
                    if args == ["cmake;3.22.1"]:
                        cmake_dir = sdk_root / "cmake"
                        cmake_dir.mkdir()
                        version_dir = cmake_dir / "3.22.1"
                        version_dir.mkdir()
                        bin_dir = version_dir / "bin"
                        bin_dir.mkdir()
                        (bin_dir / "cmake").touch()

                mock_run.side_effect = create_cmake_dir

                # Test installation
                result = manager.ensure_cmake()

                # Verify sdkmanager was called with correct arguments
                mock_run.assert_called_once_with(["cmake;3.22.1"])

                # Verify result
                assert result == sdk_root / "cmake"
                assert result.exists()
                assert (result / "3.22.1" / "bin" / "cmake").exists()

    def test_ensure_cmake_already_installed(self):
        """Test CMake when already installed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            # Pre-create cmake directory
            cmake_dir = sdk_root / "cmake"
            cmake_dir.mkdir()
            version_dir = cmake_dir / "3.22.1"
            version_dir.mkdir()

            manager = SdkManager(sdk_root, logger=logger)

            with patch.object(manager, "_run_sdkmanager") as mock_run:
                result = manager.ensure_cmake()

                # Verify sdkmanager was not called
                mock_run.assert_not_called()

                # Verify result
                assert result == cmake_dir
                assert result.exists()

    def test_cmake_installed_in_android_installer_pipeline(self):
        """Test that CMake is installed as part of AndroidInstaller pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            installer = AndroidInstaller(sdk_root, logger=logger, verbose=False)

            # Mock all the installation steps
            with patch.object(installer.sdk, "ensure_cmdline_tools"):
                with patch.object(installer.sdk, "ensure_platform_tools"):
                    with patch.object(installer.sdk, "ensure_platform"):
                        with patch.object(installer.sdk, "ensure_build_tools"):
                            with patch.object(installer.sdk, "ensure_cmake") as mock_cmake:
                                with patch.object(installer.sdk, "ensure_emulator"):
                                    with patch.object(installer.sdk, "ensure_system_image"):
                                        with patch.object(installer.sdk, "accept_licenses"):
                                            with patch.object(
                                                installer.planner, "build_plan"
                                            ) as mock_plan:
                                                # Mock plan that requires cmake installation
                                                mock_plan_obj = Mock()
                                                mock_plan_obj.need_cmdline_tools = False
                                                mock_plan_obj.need_platform_tools = True
                                                mock_plan_obj.need_platform = True
                                                mock_plan_obj.need_system_image = False
                                                mock_plan_obj.need_emulator = False
                                                mock_plan_obj.need_ndk = False
                                                mock_plan_obj.create_avd_name = None
                                                mock_plan_obj.has_work.return_value = True
                                                mock_plan.return_value = mock_plan_obj

                                                from ovmobilebench.android.installer.types import (
                                                    NdkSpec,
                                                )

                                                # Test the installation
                                                installer.ensure(
                                                    api=30,
                                                    target="google_apis",
                                                    arch="arm64-v8a",
                                                    ndk=NdkSpec(alias="r26d"),
                                                    install_build_tools="34.0.0",
                                                )

                                                # Verify CMake installation was called
                                                mock_cmake.assert_called_once()

    def test_cmake_logging(self):
        """Test CMake installation logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)
            logger = Mock()

            # Mock logger.step context manager
            logger.step.return_value.__enter__ = Mock()
            logger.step.return_value.__exit__ = Mock()

            manager = SdkManager(sdk_root, logger=logger)

            # Test when CMake already exists
            cmake_dir = sdk_root / "cmake"
            cmake_dir.mkdir()

            manager.ensure_cmake()

            # Verify debug logging for already installed
            logger.debug.assert_called_with("CMake already installed")

            # Test fresh installation
            cmake_dir.rmdir()

            with patch.object(manager, "_run_sdkmanager") as mock_run:

                def create_cmake_dir(args):
                    cmake_dir.mkdir()
                    version_dir = cmake_dir / "3.22.1"
                    version_dir.mkdir()

                mock_run.side_effect = create_cmake_dir

                # Mock logger.step context manager
                logger.step.return_value.__enter__ = Mock()
                logger.step.return_value.__exit__ = Mock()

                result = manager.ensure_cmake()

                # Verify step logging
                logger.step.assert_called_with("Installing CMake")
                logger.success.assert_called_with("CMake installed")

                # Verify result
                assert result.exists()


class TestCMakeVersionDetection:
    """Test CMake version detection in builders."""

    def test_get_cmake_executable_from_android_sdk(self):
        """Test CMake executable detection from Android SDK."""
        from ovmobilebench.builders.openvino import OpenVINOBuilder
        from ovmobilebench.config.schema import OpenVINOConfig, Toolchain

        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Create mock Android SDK structure
            ndk_dir = sdk_root / "ndk" / "26.3.11579264"
            ndk_dir.mkdir(parents=True)

            cmake_dir = sdk_root / "cmake"
            cmake_dir.mkdir()

            # Create multiple CMake versions
            cmake_3_18 = cmake_dir / "3.18.1"
            cmake_3_22 = cmake_dir / "3.22.1"
            cmake_3_25 = cmake_dir / "3.25.2"

            for version_dir in [cmake_3_18, cmake_3_22, cmake_3_25]:
                version_dir.mkdir()
                bin_dir = version_dir / "bin"
                bin_dir.mkdir()
                cmake_exe = bin_dir / "cmake"
                cmake_exe.touch()
                cmake_exe.chmod(0o755)

            # Create config with Android NDK path
            config = OpenVINOConfig(
                mode="build",
                source_dir=str(Path(temp_dir) / "source"),
                build_type="Release",
                toolchain=Toolchain(android_ndk=str(ndk_dir), abi="arm64-v8a", api_level=30),
            )

            builder = OpenVINOBuilder(config, Path(temp_dir) / "build")

            # Test CMake detection
            cmake_executable = builder._get_cmake_executable()

            # Should select the latest version (3.25.2)
            expected_cmake = str(cmake_3_25 / "bin" / "cmake")
            assert cmake_executable == expected_cmake

    def test_get_cmake_executable_fallback_to_system(self):
        """Test fallback to system CMake when Android SDK CMake not found."""
        from ovmobilebench.builders.openvino import OpenVINOBuilder
        from ovmobilebench.config.schema import OpenVINOConfig, Toolchain

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config without Android NDK
            config = OpenVINOConfig(
                mode="build",
                source_dir=str(Path(temp_dir) / "source"),
                build_type="Release",
                toolchain=Toolchain(),
            )

            builder = OpenVINOBuilder(config, Path(temp_dir) / "build")

            # Test CMake detection
            cmake_executable = builder._get_cmake_executable()

            # Should fallback to system cmake
            assert cmake_executable == "cmake"

    def test_get_cmake_executable_android_sdk_without_cmake(self):
        """Test when Android SDK exists but CMake is not installed."""
        from ovmobilebench.builders.openvino import OpenVINOBuilder
        from ovmobilebench.config.schema import OpenVINOConfig, Toolchain

        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Create Android SDK structure without CMake
            ndk_dir = sdk_root / "ndk" / "26.3.11579264"
            ndk_dir.mkdir(parents=True)

            config = OpenVINOConfig(
                mode="build",
                source_dir=str(Path(temp_dir) / "source"),
                build_type="Release",
                toolchain=Toolchain(android_ndk=str(ndk_dir), abi="arm64-v8a", api_level=30),
            )

            builder = OpenVINOBuilder(config, Path(temp_dir) / "build")

            # Test CMake detection
            cmake_executable = builder._get_cmake_executable()

            # Should fallback to system cmake
            assert cmake_executable == "cmake"

    def test_cmake_executable_logging(self):
        """Test logging of CMake executable selection."""
        from ovmobilebench.builders.openvino import OpenVINOBuilder
        from ovmobilebench.config.schema import OpenVINOConfig, Toolchain

        with tempfile.TemporaryDirectory() as temp_dir:
            sdk_root = Path(temp_dir)

            # Create mock Android SDK with CMake
            ndk_dir = sdk_root / "ndk" / "26.3.11579264"
            ndk_dir.mkdir(parents=True)

            cmake_dir = sdk_root / "cmake" / "3.22.1"
            cmake_dir.mkdir(parents=True)
            bin_dir = cmake_dir / "bin"
            bin_dir.mkdir()
            cmake_exe = bin_dir / "cmake"
            cmake_exe.touch()

            config = OpenVINOConfig(
                mode="build",
                source_dir=str(Path(temp_dir) / "source"),
                build_type="Release",
                toolchain=Toolchain(android_ndk=str(ndk_dir), abi="arm64-v8a", api_level=30),
            )

            builder = OpenVINOBuilder(config, Path(temp_dir) / "build")

            # Mock the logger to capture log calls
            with patch("ovmobilebench.builders.openvino.logger") as mock_logger:
                cmake_executable = builder._get_cmake_executable()

                # Verify appropriate logging
                expected_cmake_path = str(cmake_exe)
                mock_logger.info.assert_called_with(
                    f"Using CMake from Android SDK: {expected_cmake_path}"
                )
                assert cmake_executable == expected_cmake_path

    def test_cmake_executable_system_fallback_logging(self):
        """Test logging when falling back to system CMake."""
        from ovmobilebench.builders.openvino import OpenVINOBuilder
        from ovmobilebench.config.schema import OpenVINOConfig, Toolchain

        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenVINOConfig(
                mode="build",
                source_dir=str(Path(temp_dir) / "source"),
                build_type="Release",
                toolchain=Toolchain(),
            )

            builder = OpenVINOBuilder(config, Path(temp_dir) / "build")

            # Mock the logger to capture log calls
            with patch("ovmobilebench.builders.openvino.logger") as mock_logger:
                cmake_executable = builder._get_cmake_executable()

                # Verify appropriate logging
                mock_logger.info.assert_called_with("Using system CMake")
                assert cmake_executable == "cmake"
