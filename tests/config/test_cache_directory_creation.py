"""Test automatic cache directory creation and setup."""

from unittest.mock import call, patch

import yaml

from ovmobilebench.config.loader import (
    load_experiment,
    setup_default_paths,
)


class TestCacheDirectoryCreation:
    """Test automatic cache directory creation."""

    def test_cache_dir_created_if_not_exists(self, tmp_path):
        """Test that cache directory is created if it doesn't exist."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create config with cache_dir that doesn't exist
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "my_cache_dir"},
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root and suppress print output
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print") as mock_print:
                load_experiment(config_file)

        # Check that cache directory was created
        cache_dir = project_dir / "my_cache_dir"
        assert cache_dir.exists()
        assert cache_dir.is_dir()

        # Check that creation was logged
        mock_print.assert_any_call(f"INFO: Created cache directory: {cache_dir}")

    def test_cache_dir_not_recreated_if_exists(self, tmp_path):
        """Test that existing cache directory is not recreated."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create cache directory in advance
        cache_dir = project_dir / "existing_cache"
        cache_dir.mkdir()
        test_file = cache_dir / "test.txt"
        test_file.write_text("test content")

        # Create config
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "existing_cache"},
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root and suppress print output
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print") as mock_print:
                load_experiment(config_file)

        # Check that cache directory still exists with content
        assert cache_dir.exists()
        assert test_file.exists()
        assert test_file.read_text() == "test content"

        # Check that creation was NOT logged
        for call_args in mock_print.call_args_list:
            assert "Created cache directory" not in str(call_args)

    def test_nested_cache_dir_creation(self, tmp_path):
        """Test that nested cache directories are created."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create config with nested cache_dir
        config_data = {
            "project": {
                "name": "test",
                "run_id": "test_001",
                "cache_dir": "deeply/nested/cache/directory",
            },
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):
                load_experiment(config_file)

        # Check that nested directories were created
        cache_dir = project_dir / "deeply" / "nested" / "cache" / "directory"
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_absolute_cache_dir_creation(self, tmp_path):
        """Test that absolute cache directory paths are created."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create absolute cache path
        absolute_cache = tmp_path / "absolute_cache"

        # Create config with absolute cache_dir
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": str(absolute_cache)},
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):
                load_experiment(config_file)

        # Check that absolute directory was created
        assert absolute_cache.exists()
        assert absolute_cache.is_dir()


class TestNDKAutoDetection:
    """Test automatic NDK detection and setup."""

    def test_find_existing_ndk_in_cache(self, tmp_path):
        """Test that existing NDK is found in cache directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create NDK directory structure
        ndk_dir = project_dir / "ovmb_cache" / "android-sdk" / "ndk" / "26.3.11579264"
        ndk_dir.mkdir(parents=True)

        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "build", "toolchain": {}},
        }

        with patch("builtins.print"):
            result = setup_default_paths(config, project_dir)

        # Verify that NDK path was set
        expected_ndk = str(project_dir / "ovmb_cache" / "android-sdk" / "ndk" / "26.3.11579264")
        assert result["openvino"]["toolchain"]["android_ndk"] == expected_ndk

    def test_use_latest_ndk_version(self, tmp_path):
        """Test that latest NDK version is selected when multiple exist."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create multiple NDK versions
        ndk_base = project_dir / "ovmb_cache" / "android-sdk" / "ndk"
        (ndk_base / "25.2.9519653").mkdir(parents=True)
        (ndk_base / "26.3.11579264").mkdir(parents=True)
        (ndk_base / "27.2.12479018").mkdir(parents=True)

        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "build", "toolchain": {}},
        }

        with patch("builtins.print"):
            result = setup_default_paths(config, project_dir)

        # Should select the latest version
        expected_ndk = str(project_dir / "ovmb_cache" / "android-sdk" / "ndk" / "27.2.12479018")
        assert result["openvino"]["toolchain"]["android_ndk"] == expected_ndk

    def test_ndk_not_found_message(self, tmp_path):
        """Test that helpful message is shown when NDK is not found."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "build", "toolchain": {}},
        }

        with patch("builtins.print") as mock_print:
            setup_default_paths(config, project_dir)

        # Check that installation instructions were printed
        cache_path = project_dir / "ovmb_cache"
        expected_calls = [
            call("INFO: No android_ndk specified and no NDK found"),
            call("INFO: Android NDK not found. Install it with:"),
            call(
                f"      python -m ovmobilebench.cli setup-android --sdk-root {cache_path}/android-sdk"
            ),
            call("      # This will install the latest available NDK version"),
            call("      # Or specify a specific NDK version:"),
            call(
                f"      python -m ovmobilebench.cli setup-android --sdk-root {cache_path}/android-sdk --ndk-version <version>"
            ),
        ]

        for expected_call in expected_calls:
            assert expected_call in mock_print.call_args_list


class TestOpenVINOAutoSetup:
    """Test automatic OpenVINO setup."""

    def test_openvino_source_not_found_message(self, tmp_path):
        """Test that helpful message is shown when OpenVINO source is not found."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        config = {"project": {"cache_dir": "ovmb_cache"}, "openvino": {"mode": "build"}}

        with patch("builtins.print") as mock_print:
            setup_default_paths(config, project_dir)

        # Check that clone instructions were printed
        cache_path = project_dir / "ovmb_cache"
        expected_source = cache_path / "openvino_source"

        expected_calls = [
            call(f"INFO: No source_dir specified, using default: {expected_source}"),
            call("INFO: OpenVINO source not found. Clone it with:"),
            call(
                f"      git clone https://github.com/openvinotoolkit/openvino.git {expected_source}"
            ),
        ]

        for expected_call in expected_calls:
            assert expected_call in mock_print.call_args_list

    def test_openvino_source_exists_no_message(self, tmp_path):
        """Test that no clone message is shown when OpenVINO source exists."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create OpenVINO source directory
        openvino_source = project_dir / "ovmb_cache" / "openvino_source"
        openvino_source.mkdir(parents=True)

        config = {"project": {"cache_dir": "ovmb_cache"}, "openvino": {"mode": "build"}}

        with patch("builtins.print") as mock_print:
            setup_default_paths(config, project_dir)

        # Check that clone instructions were NOT printed
        for call_args in mock_print.call_args_list:
            assert "Clone it with" not in str(call_args)
