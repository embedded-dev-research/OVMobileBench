"""Test OpenVINOBuilder with new CMake options structure."""

from unittest.mock import MagicMock, patch

from ovmobilebench.builders.openvino import OpenVINOBuilder
from ovmobilebench.config.schema import BuildOptions, OpenVINOConfig, Toolchain


class TestOpenVINOBuilderCMakeOptions:
    """Test OpenVINOBuilder with CMake options."""

    def test_cmake_args_with_options(self, tmp_path):
        """Test that CMake args are correctly built from options."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(
                CMAKE_BUILD_TYPE="Debug",
                CMAKE_GENERATOR="Ninja",
                ENABLE_INTEL_GPU="ON",
                ENABLE_TESTS="ON",
            ),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):  # No ccache or ninja
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        # Check the cmake command
        cmake_args = mock_run.call_args[0][0]

        # Should have source and build directories
        assert "-S" in cmake_args
        assert "/path/to/openvino" in cmake_args
        assert "-B" in cmake_args
        assert str(build_dir) in cmake_args

        # Should have OUTPUT_ROOT
        assert f"-DOUTPUT_ROOT={build_dir}" in cmake_args

        # Should have generator
        assert "-G" in cmake_args
        assert "Ninja" in cmake_args

        # Should have all options as -D flags
        assert "-DCMAKE_BUILD_TYPE=Debug" in cmake_args
        assert "-DENABLE_INTEL_GPU=ON" in cmake_args
        assert "-DENABLE_TESTS=ON" in cmake_args
        assert "-DENABLE_SAMPLES=ON" in cmake_args  # Default value

    def test_cmake_generator_from_options(self, tmp_path):
        """Test that CMAKE_GENERATOR is correctly handled."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(CMAKE_GENERATOR="Unix Makefiles"),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should have the generator
        assert "-G" in cmake_args
        assert "Unix Makefiles" in cmake_args

        # CMAKE_GENERATOR should not be in -D options
        assert "-DCMAKE_GENERATOR=Unix Makefiles" not in cmake_args

    def test_android_toolchain_options_from_config(self, tmp_path):
        """Test that Android toolchain options are set from config."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            toolchain=Toolchain(android_ndk="/path/to/ndk", abi="arm64-v8a", api_level=30),
            options=BuildOptions(),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should have Android toolchain options
        assert (
            "-DCMAKE_TOOLCHAIN_FILE=/path/to/ndk/build/cmake/android.toolchain.cmake" in cmake_args
        )
        assert "-DANDROID_ABI=arm64-v8a" in cmake_args
        assert "-DANDROID_PLATFORM=android-30" in cmake_args
        assert "-DANDROID_STL=c++_shared" in cmake_args

    def test_android_options_override_from_options(self, tmp_path):
        """Test that Android options from options override toolchain settings."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            toolchain=Toolchain(android_ndk="/path/to/ndk", abi="arm64-v8a", api_level=30),
            options=BuildOptions(
                ANDROID_ABI="x86_64",  # Override
                ANDROID_PLATFORM="android-31",  # Override
                ANDROID_STL="c++_static",  # Override
            ),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should use overridden values from options
        assert "-DANDROID_ABI=x86_64" in cmake_args
        assert "-DANDROID_PLATFORM=android-31" in cmake_args
        assert "-DANDROID_STL=c++_static" in cmake_args

        # Should not have the toolchain defaults
        assert "-DANDROID_ABI=arm64-v8a" not in cmake_args
        assert "-DANDROID_PLATFORM=android-30" not in cmake_args
        assert "-DANDROID_STL=c++_shared" not in cmake_args


class TestCCacheAutoDetection:
    """Test ccache auto-detection."""

    def test_ccache_auto_detected(self, tmp_path):
        """Test that ccache is auto-detected when available."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(),  # No ccache specified
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = lambda cmd: "/usr/bin/ccache" if cmd == "ccache" else None
                mock_run.return_value = MagicMock(returncode=0)

                with patch("ovmobilebench.builders.openvino.logger") as mock_logger:
                    builder._configure_cmake()
                    mock_logger.info.assert_any_call("Auto-detected ccache for compilation")

        cmake_args = mock_run.call_args[0][0]

        # Should have ccache options
        assert "-DCMAKE_C_COMPILER_LAUNCHER=ccache" in cmake_args
        assert "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache" in cmake_args

    def test_ccache_not_detected_when_unavailable(self, tmp_path):
        """Test that ccache is not used when unavailable."""
        config = OpenVINOConfig(
            mode="build", source_dir="/path/to/openvino", options=BuildOptions()
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):  # No ccache
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should not have ccache options
        assert "-DCMAKE_C_COMPILER_LAUNCHER=ccache" not in cmake_args
        assert "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache" not in cmake_args

    def test_ccache_explicit_in_options(self, tmp_path):
        """Test that explicit ccache in options is used regardless of detection."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(
                CMAKE_C_COMPILER_LAUNCHER="distcc", CMAKE_CXX_COMPILER_LAUNCHER="distcc"
            ),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which") as mock_which:
                # ccache is available but we use distcc from options
                mock_which.side_effect = lambda cmd: "/usr/bin/ccache" if cmd == "ccache" else None
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should use distcc from options, not auto-detected ccache
        assert "-DCMAKE_C_COMPILER_LAUNCHER=distcc" in cmake_args
        assert "-DCMAKE_CXX_COMPILER_LAUNCHER=distcc" in cmake_args
        assert "-DCMAKE_C_COMPILER_LAUNCHER=ccache" not in cmake_args


class TestNinjaAutoDetection:
    """Test Ninja auto-detection."""

    def test_ninja_auto_detected(self, tmp_path):
        """Test that Ninja is auto-detected when available and no generator specified."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(),  # No CMAKE_GENERATOR specified
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which") as mock_which:
                mock_which.side_effect = lambda cmd: "/usr/bin/ninja" if cmd == "ninja" else None
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should have Ninja generator
        assert "-G" in cmake_args
        assert "Ninja" in cmake_args

    def test_ninja_not_used_when_unavailable(self, tmp_path):
        """Test that Ninja is not used when unavailable."""
        config = OpenVINOConfig(
            mode="build", source_dir="/path/to/openvino", options=BuildOptions()
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):  # No ninja
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should not have -G flag (use CMake default)
        assert "-G" not in cmake_args

    def test_explicit_generator_overrides_auto_detection(self, tmp_path):
        """Test that explicit generator in options overrides auto-detection."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(CMAKE_GENERATOR="Unix Makefiles"),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which") as mock_which:
                # Ninja is available but we use Unix Makefiles from options
                mock_which.side_effect = lambda cmd: "/usr/bin/ninja" if cmd == "ninja" else None
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Should use Unix Makefiles from options
        assert "-G" in cmake_args
        assert "Unix Makefiles" in cmake_args
        assert "Ninja" not in cmake_args


class TestCMakeExecutableDetection:
    """Test CMake executable detection."""

    def test_cmake_from_android_sdk(self, tmp_path):
        """Test that CMake from Android SDK is preferred."""
        ndk_path = tmp_path / "android-sdk" / "ndk" / "26.3.11579264"
        ndk_path.mkdir(parents=True)

        cmake_dir = tmp_path / "android-sdk" / "cmake" / "3.22.1" / "bin"
        cmake_dir.mkdir(parents=True)
        cmake_executable = cmake_dir / "cmake"
        cmake_executable.touch()

        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            toolchain=Toolchain(android_ndk=str(ndk_path)),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        result = builder._get_cmake_executable()
        assert result == str(cmake_executable)

    def test_cmake_fallback_to_system(self, tmp_path):
        """Test fallback to system cmake when Android SDK cmake not found."""
        config = OpenVINOConfig(mode="build", source_dir="/path/to/openvino")

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        result = builder._get_cmake_executable()
        assert result == "cmake"


class TestOptionsIntegration:
    """Test full integration of options with builder."""

    def test_full_android_build_configuration(self, tmp_path):
        """Test complete Android build configuration with all options."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            toolchain=Toolchain(android_ndk="/path/to/ndk", abi="arm64-v8a", api_level=30),
            options=BuildOptions(
                CMAKE_BUILD_TYPE="Release",
                CMAKE_GENERATOR="Ninja",
                CMAKE_C_COMPILER_LAUNCHER="ccache",
                CMAKE_CXX_COMPILER_LAUNCHER="ccache",
                ENABLE_INTEL_GPU="OFF",
                ENABLE_ONEDNN_FOR_ARM="ON",
                ENABLE_PYTHON="OFF",
                BUILD_SHARED_LIBS="ON",
                ENABLE_TESTS="OFF",
                ENABLE_FUNCTIONAL_TESTS="OFF",
                ENABLE_SAMPLES="ON",
                ENABLE_OPENCV="OFF",
            ),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            builder._configure_cmake()

        cmake_args = mock_run.call_args[0][0]

        # Check all expected arguments are present
        expected_args = [
            "-S",
            "/path/to/openvino",
            "-B",
            str(build_dir),
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_C_COMPILER_LAUNCHER=ccache",
            "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache",
            "-DCMAKE_TOOLCHAIN_FILE=/path/to/ndk/build/cmake/android.toolchain.cmake",
            "-DANDROID_ABI=arm64-v8a",
            "-DANDROID_PLATFORM=android-30",
            "-DANDROID_STL=c++_shared",
            "-DENABLE_INTEL_GPU=OFF",
            "-DENABLE_ONEDNN_FOR_ARM=ON",
            "-DENABLE_PYTHON=OFF",
            "-DBUILD_SHARED_LIBS=ON",
            "-DENABLE_TESTS=OFF",
            "-DENABLE_FUNCTIONAL_TESTS=OFF",
            "-DENABLE_SAMPLES=ON",
            "-DENABLE_OPENCV=OFF",
        ]

        for arg in expected_args:
            assert arg in cmake_args, f"Missing argument: {arg}"

    def test_options_with_none_values_skipped(self, tmp_path):
        """Test that options with None values are not added to cmake args."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(
                CMAKE_BUILD_TYPE="Release",
                CMAKE_C_COMPILER_LAUNCHER=None,  # Should be skipped
                CMAKE_CXX_COMPILER_LAUNCHER=None,  # Should be skipped
                CMAKE_GENERATOR=None,  # Should be skipped
            ),
        )

        build_dir = tmp_path / "build"
        builder = OpenVINOBuilder(config, build_dir)

        with patch("ovmobilebench.builders.openvino.run") as mock_run:
            with patch("shutil.which", return_value=None):
                mock_run.return_value = MagicMock(returncode=0)
                builder._configure_cmake()

        cmake_args_str = " ".join(mock_run.call_args[0][0])

        # Should have CMAKE_BUILD_TYPE
        assert "-DCMAKE_BUILD_TYPE=Release" in cmake_args_str

        # Should not have None values
        assert "CMAKE_C_COMPILER_LAUNCHER=None" not in cmake_args_str
        assert "CMAKE_CXX_COMPILER_LAUNCHER=None" not in cmake_args_str
        assert "CMAKE_GENERATOR=None" not in cmake_args_str
