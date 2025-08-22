"""Test environment configuration functionality."""

import os
from pathlib import Path
from unittest.mock import patch

import yaml

from ovmobilebench.config.loader import (
    load_experiment,
    setup_environment,
)


class TestEnvironmentConfig:
    """Test environment configuration setup."""

    def test_java_home_setup(self, tmp_path):
        """Test that JAVA_HOME is set from config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"environment": {"java_home": "/opt/java/jdk-17"}}

        # Clear JAVA_HOME if it exists
        original_java_home = os.environ.get("JAVA_HOME")
        original_path = os.environ.get("PATH", "")

        try:
            if "JAVA_HOME" in os.environ:
                del os.environ["JAVA_HOME"]

            with patch("builtins.print"):
                setup_environment(config, project_dir)

            # Check that JAVA_HOME was set
            assert os.environ.get("JAVA_HOME") == "/opt/java/jdk-17"
            # Check that Java bin was added to PATH
            # Use os.path.join to get platform-appropriate path
            java_bin = os.path.join("/opt/java/jdk-17", "bin")
            current_path = os.environ.get("PATH", "")
            # Check if path is in PATH with either separator style
            java_bin_unix = "/opt/java/jdk-17/bin"
            java_bin_win = "\\opt\\java\\jdk-17\\bin"
            assert (
                java_bin in current_path
                or java_bin_unix in current_path
                or java_bin_win in current_path
            )
            # No print expected when java_home is explicitly set in config

        finally:
            # Restore original environment
            if original_java_home:
                os.environ["JAVA_HOME"] = original_java_home
            else:
                os.environ.pop("JAVA_HOME", None)
            os.environ["PATH"] = original_path

    def test_sdk_root_setup(self, tmp_path):
        """Test that Android SDK root is set from config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"environment": {"sdk_root": "/home/user/android-sdk"}}

        # Save original environment
        original_android_home = os.environ.get("ANDROID_HOME")
        original_android_sdk_root = os.environ.get("ANDROID_SDK_ROOT")

        try:
            with patch("builtins.print"):
                setup_environment(config, project_dir)

            # Check that Android environment was set
            assert os.environ.get("ANDROID_HOME") == "/home/user/android-sdk"
            assert os.environ.get("ANDROID_SDK_ROOT") == "/home/user/android-sdk"
            # No print expected when sdk_root is explicitly set in config

        finally:
            # Restore original environment
            if original_android_home:
                os.environ["ANDROID_HOME"] = original_android_home
            else:
                os.environ.pop("ANDROID_HOME", None)
            if original_android_sdk_root:
                os.environ["ANDROID_SDK_ROOT"] = original_android_sdk_root
            else:
                os.environ.pop("ANDROID_SDK_ROOT", None)

    def test_both_java_and_sdk_setup(self, tmp_path):
        """Test setting both Java and SDK from config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {
            "environment": {"java_home": "/usr/lib/jvm/java-17", "sdk_root": "/opt/android-sdk"}
        }

        # Save original environment
        original_env = {
            "JAVA_HOME": os.environ.get("JAVA_HOME"),
            "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
            "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
            "PATH": os.environ.get("PATH", ""),
        }

        try:
            with patch("builtins.print"):
                setup_environment(config, project_dir)

            # Check that all environment variables were set
            assert os.environ.get("JAVA_HOME") == "/usr/lib/jvm/java-17"
            assert os.environ.get("ANDROID_HOME") == "/opt/android-sdk"
            assert os.environ.get("ANDROID_SDK_ROOT") == "/opt/android-sdk"
            # Check that Java bin was added to PATH
            java_bin = os.path.join("/usr/lib/jvm/java-17", "bin")
            current_path = os.environ.get("PATH", "")
            # Check if path is in PATH with either separator style
            java_bin_unix = "/usr/lib/jvm/java-17/bin"
            java_bin_win = "\\usr\\lib\\jvm\\java-17\\bin"
            assert (
                java_bin in current_path
                or java_bin_unix in current_path
                or java_bin_win in current_path
            )

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

    def test_no_environment_section(self, tmp_path):
        """Test that missing environment section doesn't cause errors."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"project": {"name": "test"}}

        # Should not raise any errors
        with patch("builtins.print"):
            result = setup_environment(config, project_dir)

        # Environment section should be created with auto-detected values
        assert "environment" in result
        assert result["project"] == {"name": "test"}

    def test_empty_environment_section(self, tmp_path):
        """Test that empty environment section is handled correctly."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"environment": {}}

        # Should not raise any errors
        with patch("builtins.print"):
            result = setup_environment(config, project_dir)

        # Environment section should have auto-detected values
        assert "environment" in result
        # SDK root should be auto-detected to cache_dir/android-sdk
        assert "sdk_root" in result["environment"]


class TestEnvironmentInExperiment:
    """Test environment configuration in full experiment loading."""

    def test_load_experiment_with_environment(self, tmp_path):
        """Test loading experiment with environment configuration."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create config with environment
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "cache"},
            "environment": {"java_home": "/opt/java/jdk-17", "sdk_root": "/opt/android-sdk"},
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Save original environment
        original_env = {
            "JAVA_HOME": os.environ.get("JAVA_HOME"),
            "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
            "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
            "PATH": os.environ.get("PATH", ""),
        }

        try:
            # Mock get_project_root
            with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
                with patch("builtins.print"):
                    experiment = load_experiment(config_file)

            # Check that experiment was loaded
            assert experiment.environment.java_home == "/opt/java/jdk-17"
            assert experiment.environment.sdk_root == "/opt/android-sdk"

            # Check that environment variables were set
            assert os.environ.get("JAVA_HOME") == "/opt/java/jdk-17"
            assert os.environ.get("ANDROID_HOME") == "/opt/android-sdk"

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

    def test_ci_style_config(self, tmp_path):
        """Test CI-style configuration with absolute paths."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create CI-style config
        home_dir = Path.home()
        config_data = {
            "project": {
                "name": "e2e-android-resnet50",
                "run_id": "ci_123",
                "description": "CI E2E test",
                "cache_dir": str(home_dir / "ovmb_cache"),
            },
            "environment": {
                "java_home": "/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.8/x64",
                "sdk_root": str(home_dir / "ovmb_cache" / "android-sdk"),
            },
            "openvino": {
                "mode": "build",
                "commit": "HEAD",
                "build_type": "Release",
                "toolchain": {"abi": "arm64-v8a", "api_level": 30, "ninja": "ninja"},
                "options": {
                    "ENABLE_INTEL_GPU": "OFF",
                    "ENABLE_ONEDNN_FOR_ARM": "OFF",
                    "ENABLE_PYTHON": "OFF",
                    "BUILD_SHARED_LIBS": "ON",
                },
            },
            "device": {
                "kind": "android",
                "serials": ["emulator-5554"],
                "push_dir": "/data/local/tmp/ovmobilebench",
                "use_root": False,
            },
            "models": [
                {
                    "name": "resnet-50",
                    "path": str(home_dir / "ovmb_cache" / "models" / "resnet-50-pytorch.xml"),
                }
            ],
            "report": {"sinks": [{"type": "json", "path": "artifacts/reports/results.json"}]},
        }

        config_file = project_dir / "ci_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Save original environment
        original_env = {
            "JAVA_HOME": os.environ.get("JAVA_HOME"),
            "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
            "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
        }

        try:
            # Mock get_project_root
            with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
                with patch("builtins.print"):
                    experiment = load_experiment(config_file)

            # Check that experiment was loaded with CI paths
            assert (
                experiment.environment.java_home
                == "/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.8/x64"
            )
            # Use Path to normalize for platform
            expected_sdk = str(Path(home_dir) / "ovmb_cache" / "android-sdk")
            assert experiment.environment.sdk_root == expected_sdk
            expected_cache = str(Path(home_dir) / "ovmb_cache")
            assert experiment.project.cache_dir == expected_cache

            # Check that environment variables were set
            assert (
                os.environ.get("JAVA_HOME")
                == "/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.8/x64"
            )
            # On Windows, paths in environment use backslashes
            expected_android_home = str(Path(home_dir) / "ovmb_cache" / "android-sdk")
            assert os.environ.get("ANDROID_HOME") == expected_android_home

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)

    def test_avd_home_setup(self, tmp_path):
        """Test that AVD home is set from config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"environment": {"sdk_root": "/opt/android-sdk", "avd_home": "/custom/avd"}}

        # Save original environment
        original_avd_home = os.environ.get("ANDROID_AVD_HOME")

        try:
            with patch("builtins.print"):
                setup_environment(config, project_dir)

            # Check that AVD home was set
            assert os.environ.get("ANDROID_AVD_HOME") == "/custom/avd"

        finally:
            # Restore original environment
            if original_avd_home:
                os.environ["ANDROID_AVD_HOME"] = original_avd_home
            else:
                os.environ.pop("ANDROID_AVD_HOME", None)

    def test_avd_home_auto_setup(self, tmp_path):
        """Test that AVD home is auto-set based on SDK root."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"environment": {"sdk_root": "/opt/android-sdk"}}

        # Save original environment
        original_env = {
            "ANDROID_AVD_HOME": os.environ.get("ANDROID_AVD_HOME"),
            "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
            "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
        }

        try:
            # Clear environment to ensure clean test
            for key in original_env.keys():
                os.environ.pop(key, None)

            with patch("builtins.print"):
                result = setup_environment(config, project_dir)

            # Check that AVD home was auto-set based on SDK root
            # Use os.path.join to get platform-appropriate path
            expected_avd_home = os.path.join("/opt/android-sdk", ".android", "avd")
            assert result["environment"]["avd_home"] == expected_avd_home
            assert os.environ.get("ANDROID_AVD_HOME") == expected_avd_home

        finally:
            # Restore original environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)
