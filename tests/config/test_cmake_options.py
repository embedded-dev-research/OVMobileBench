"""Test CMake options configuration."""

from unittest.mock import patch

import yaml

from ovmobilebench.config.loader import load_experiment
from ovmobilebench.config.schema import BuildOptions, OpenVINOConfig, Toolchain


class TestBuildOptions:
    """Test BuildOptions configuration."""

    def test_default_build_options(self):
        """Test default BuildOptions values."""
        options = BuildOptions()

        assert options.CMAKE_BUILD_TYPE == "Release"
        assert options.CMAKE_C_COMPILER_LAUNCHER is None
        assert options.CMAKE_CXX_COMPILER_LAUNCHER is None
        assert options.CMAKE_GENERATOR is None
        assert options.CMAKE_TOOLCHAIN_FILE is None
        assert options.ANDROID_ABI is None
        assert options.ANDROID_PLATFORM is None
        assert options.ANDROID_STL is None
        assert options.ENABLE_INTEL_GPU == "OFF"
        assert options.ENABLE_ONEDNN_FOR_ARM == "OFF"
        assert options.ENABLE_PYTHON == "OFF"
        assert options.BUILD_SHARED_LIBS == "ON"
        assert options.ENABLE_TESTS == "OFF"
        assert options.ENABLE_FUNCTIONAL_TESTS == "OFF"
        assert options.ENABLE_SAMPLES == "ON"
        assert options.ENABLE_OPENCV == "OFF"

    def test_custom_build_options(self):
        """Test custom BuildOptions values."""
        options = BuildOptions(
            CMAKE_BUILD_TYPE="Debug",
            CMAKE_C_COMPILER_LAUNCHER="ccache",
            CMAKE_CXX_COMPILER_LAUNCHER="ccache",
            CMAKE_GENERATOR="Ninja",
            CMAKE_TOOLCHAIN_FILE="/path/to/toolchain.cmake",
            ANDROID_ABI="arm64-v8a",
            ANDROID_PLATFORM="android-30",
            ANDROID_STL="c++_shared",
            ENABLE_INTEL_GPU="ON",
            ENABLE_TESTS="ON",
        )

        assert options.CMAKE_BUILD_TYPE == "Debug"
        assert options.CMAKE_C_COMPILER_LAUNCHER == "ccache"
        assert options.CMAKE_CXX_COMPILER_LAUNCHER == "ccache"
        assert options.CMAKE_GENERATOR == "Ninja"
        assert options.CMAKE_TOOLCHAIN_FILE == "/path/to/toolchain.cmake"
        assert options.ANDROID_ABI == "arm64-v8a"
        assert options.ANDROID_PLATFORM == "android-30"
        assert options.ANDROID_STL == "c++_shared"
        assert options.ENABLE_INTEL_GPU == "ON"
        assert options.ENABLE_TESTS == "ON"

    def test_build_options_model_dump(self):
        """Test BuildOptions model_dump method."""
        options = BuildOptions(CMAKE_BUILD_TYPE="RelWithDebInfo", CMAKE_GENERATOR="Unix Makefiles")

        dump = options.model_dump()
        assert dump["CMAKE_BUILD_TYPE"] == "RelWithDebInfo"
        assert dump["CMAKE_GENERATOR"] == "Unix Makefiles"
        assert dump["CMAKE_C_COMPILER_LAUNCHER"] is None
        assert dump["ENABLE_SAMPLES"] == "ON"


class TestOpenVINOConfigWithOptions:
    """Test OpenVINOConfig with BuildOptions."""

    def test_openvino_config_with_default_options(self):
        """Test OpenVINOConfig with default BuildOptions."""
        config = OpenVINOConfig(mode="build", source_dir="/path/to/openvino")

        assert config.options.CMAKE_BUILD_TYPE == "Release"
        assert config.options.ENABLE_SAMPLES == "ON"
        assert config.options.CMAKE_GENERATOR is None

    def test_openvino_config_with_custom_options(self):
        """Test OpenVINOConfig with custom BuildOptions."""
        config = OpenVINOConfig(
            mode="build",
            source_dir="/path/to/openvino",
            options=BuildOptions(
                CMAKE_BUILD_TYPE="Debug",
                CMAKE_GENERATOR="Ninja",
                CMAKE_C_COMPILER_LAUNCHER="ccache",
            ),
        )

        assert config.options.CMAKE_BUILD_TYPE == "Debug"
        assert config.options.CMAKE_GENERATOR == "Ninja"
        assert config.options.CMAKE_C_COMPILER_LAUNCHER == "ccache"

    def test_openvino_config_no_build_type_field(self):
        """Test that build_type field no longer exists in OpenVINOConfig."""
        config = OpenVINOConfig(mode="build", source_dir="/path/to/openvino")

        # build_type should not be an attribute of OpenVINOConfig
        assert not hasattr(config, "build_type")
        # It should be in options instead
        assert hasattr(config.options, "CMAKE_BUILD_TYPE")


class TestToolchainWithoutCMakeNinja:
    """Test Toolchain without cmake and ninja fields."""

    def test_toolchain_no_cmake_ninja_fields(self):
        """Test that cmake and ninja fields no longer exist in Toolchain."""
        toolchain = Toolchain(android_ndk="/path/to/ndk", abi="arm64-v8a", api_level=30)

        # cmake and ninja should not be attributes of Toolchain
        assert not hasattr(toolchain, "cmake")
        assert not hasattr(toolchain, "ninja")

        # Only android_ndk, abi, and api_level should exist
        assert toolchain.android_ndk == "/path/to/ndk"
        assert toolchain.abi == "arm64-v8a"
        assert toolchain.api_level == 30

    def test_toolchain_default_factory(self):
        """Test Toolchain default factory."""
        config = OpenVINOConfig(mode="build")

        assert config.toolchain.android_ndk is None
        assert config.toolchain.abi == "arm64-v8a"
        assert config.toolchain.api_level == 24
        assert not hasattr(config.toolchain, "cmake")
        assert not hasattr(config.toolchain, "ninja")


class TestConfigLoading:
    """Test loading configurations with new options structure."""

    def test_load_config_with_cmake_options(self, tmp_path):
        """Test loading config with CMake options."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "cache"},
            "openvino": {
                "mode": "build",
                "toolchain": {"abi": "arm64-v8a", "api_level": 30},
                "options": {
                    "CMAKE_BUILD_TYPE": "Debug",
                    "CMAKE_GENERATOR": "Ninja",
                    "CMAKE_C_COMPILER_LAUNCHER": "ccache",
                    "CMAKE_CXX_COMPILER_LAUNCHER": "ccache",
                    "ENABLE_INTEL_GPU": "ON",
                    "ENABLE_TESTS": "ON",
                },
            },
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):
                experiment = load_experiment(config_file)

        assert experiment.openvino.options.CMAKE_BUILD_TYPE == "Debug"
        assert experiment.openvino.options.CMAKE_GENERATOR == "Ninja"
        assert experiment.openvino.options.CMAKE_C_COMPILER_LAUNCHER == "ccache"
        assert experiment.openvino.options.CMAKE_CXX_COMPILER_LAUNCHER == "ccache"
        assert experiment.openvino.options.ENABLE_INTEL_GPU == "ON"
        assert experiment.openvino.options.ENABLE_TESTS == "ON"

    def test_load_config_without_options(self, tmp_path):
        """Test loading config without options section uses defaults."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "cache"},
            "openvino": {
                "mode": "build",
                "toolchain": {"abi": "arm64-v8a", "api_level": 30},
                # No options section
            },
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):
                experiment = load_experiment(config_file)

        # Should use default values
        assert experiment.openvino.options.CMAKE_BUILD_TYPE == "Release"
        assert experiment.openvino.options.CMAKE_GENERATOR is None
        assert experiment.openvino.options.ENABLE_SAMPLES == "ON"
        assert experiment.openvino.options.ENABLE_TESTS == "OFF"

    def test_backward_compatibility_no_build_type(self, tmp_path):
        """Test that configs with build_type in wrong place fail gracefully."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "cache"},
            "openvino": {
                "mode": "build",
                "build_type": "Debug",  # Old location - should be ignored
                "toolchain": {"abi": "arm64-v8a", "api_level": 30},
                "options": {"CMAKE_BUILD_TYPE": "Release"},  # New location
            },
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):
                # This should work but ignore the old build_type field
                experiment = load_experiment(config_file)

        # Should use the value from options, not the old field
        assert experiment.openvino.options.CMAKE_BUILD_TYPE == "Release"
        assert not hasattr(experiment.openvino, "build_type")
