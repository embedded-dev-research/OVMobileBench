"""Test path resolution functionality in configuration loader."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ovmobilebench.config.loader import (
    get_project_root,
    load_experiment,
    resolve_path,
    resolve_paths_in_config,
)


class TestPathResolution:
    """Test path resolution functionality."""

    def test_resolve_absolute_path(self):
        """Test that absolute paths are returned unchanged."""
        project_root = Path("/home/user/project")
        absolute_path = "/opt/android-sdk"

        result = resolve_path(absolute_path, project_root)
        assert result == absolute_path

    def test_resolve_relative_path(self):
        """Test that relative paths are resolved from project root."""
        project_root = Path("/home/user/project")
        relative_path = "ovmb_cache/android-sdk"

        result = resolve_path(relative_path, project_root)
        assert result == "/home/user/project/ovmb_cache/android-sdk"

    def test_resolve_empty_path(self):
        """Test that empty paths are returned unchanged."""
        project_root = Path("/home/user/project")

        assert resolve_path("", project_root) == ""
        assert resolve_path(None, project_root) is None

    def test_resolve_path_with_dots(self):
        """Test resolution of paths with .. and ."""
        project_root = Path("/home/user/project")

        result = resolve_path("./ovmb_cache/sdk", project_root)
        assert result == "/home/user/project/ovmb_cache/sdk"

        result = resolve_path("../external/sdk", project_root)
        assert result == "/home/user/external/sdk"


class TestConfigPathResolution:
    """Test path resolution in configuration dictionaries."""

    def test_resolve_openvino_source_dir(self):
        """Test resolution of OpenVINO source_dir."""
        project_root = Path("/home/user/project")
        config = {"openvino": {"mode": "build", "source_dir": "ovmb_cache/openvino_source"}}

        result = resolve_paths_in_config(config, project_root)
        assert result["openvino"]["source_dir"] == "/home/user/project/ovmb_cache/openvino_source"

    def test_resolve_openvino_install_dir(self):
        """Test resolution of OpenVINO install_dir."""
        project_root = Path("/home/user/project")
        config = {"openvino": {"mode": "install", "install_dir": "ovmb_cache/openvino_install"}}

        result = resolve_paths_in_config(config, project_root)
        assert result["openvino"]["install_dir"] == "/home/user/project/ovmb_cache/openvino_install"

    def test_resolve_android_ndk(self):
        """Test resolution of Android NDK path."""
        project_root = Path("/home/user/project")
        config = {
            "openvino": {"toolchain": {"android_ndk": "ovmb_cache/android-sdk/ndk/26.3.11579264"}}
        }

        result = resolve_paths_in_config(config, project_root)
        expected = "/home/user/project/ovmb_cache/android-sdk/ndk/26.3.11579264"
        assert result["openvino"]["toolchain"]["android_ndk"] == expected

    def test_resolve_model_paths_list(self):
        """Test resolution of model paths in list format."""
        project_root = Path("/home/user/project")
        config = {
            "models": [
                {"name": "model1", "path": "ovmb_cache/models/model1.xml"},
                {"name": "model2", "path": "/absolute/path/model2.xml"},
            ]
        }

        result = resolve_paths_in_config(config, project_root)
        assert result["models"][0]["path"] == "/home/user/project/ovmb_cache/models/model1.xml"
        assert result["models"][1]["path"] == "/absolute/path/model2.xml"

    def test_resolve_model_directories(self):
        """Test resolution of model directories."""
        project_root = Path("/home/user/project")
        config = {
            "models": {
                "directories": ["ovmb_cache/models", "/absolute/models"],
                "models": [{"name": "model1", "path": "ovmb_cache/models/model1.xml"}],
            }
        }

        result = resolve_paths_in_config(config, project_root)
        assert result["models"]["directories"][0] == "/home/user/project/ovmb_cache/models"
        assert result["models"]["directories"][1] == "/absolute/models"
        assert (
            result["models"]["models"][0]["path"]
            == "/home/user/project/ovmb_cache/models/model1.xml"
        )

    def test_resolve_cache_dir(self):
        """Test resolution of project cache_dir."""
        project_root = Path("/home/user/project")
        config = {"project": {"name": "test", "cache_dir": "ovmb_cache"}}

        result = resolve_paths_in_config(config, project_root)
        assert result["project"]["cache_dir"] == "/home/user/project/ovmb_cache"

    def test_resolve_report_paths(self):
        """Test resolution of report sink paths."""
        project_root = Path("/home/user/project")
        config = {
            "report": {
                "sinks": [
                    {"type": "json", "path": "artifacts/results.json"},
                    {"type": "csv", "path": "/absolute/results.csv"},
                ]
            }
        }

        result = resolve_paths_in_config(config, project_root)
        assert result["report"]["sinks"][0]["path"] == "/home/user/project/artifacts/results.json"
        assert result["report"]["sinks"][1]["path"] == "/absolute/results.csv"

    def test_preserve_none_values(self):
        """Test that None values are preserved."""
        project_root = Path("/home/user/project")
        config = {
            "openvino": {
                "source_dir": None,
                "install_dir": None,
                "toolchain": {"android_ndk": None},
            }
        }

        result = resolve_paths_in_config(config, project_root)
        assert result["openvino"]["source_dir"] is None
        assert result["openvino"]["install_dir"] is None
        assert result["openvino"]["toolchain"]["android_ndk"] is None

    def test_config_not_modified(self):
        """Test that original config is not modified."""
        project_root = Path("/home/user/project")
        config = {"openvino": {"source_dir": "ovmb_cache/openvino"}}
        original_source_dir = config["openvino"]["source_dir"]

        result = resolve_paths_in_config(config, project_root)

        # Original should be unchanged
        assert config["openvino"]["source_dir"] == original_source_dir
        # Result should be resolved
        assert result["openvino"]["source_dir"] == "/home/user/project/ovmb_cache/openvino"


class TestProjectRootDetection:
    """Test project root detection."""

    def test_find_project_root_with_pyproject(self, tmp_path):
        """Test finding project root by pyproject.toml."""
        # Create directory structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        subdir = project_dir / "subdir"
        subdir.mkdir()

        # Create pyproject.toml
        (project_dir / "pyproject.toml").touch()

        # Change to subdirectory
        with patch("pathlib.Path.cwd", return_value=subdir):
            root = get_project_root()
            assert root == project_dir

    def test_find_project_root_with_setup_py(self, tmp_path):
        """Test finding project root by setup.py."""
        # Create directory structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        subdir = project_dir / "subdir"
        subdir.mkdir()

        # Create setup.py
        (project_dir / "setup.py").touch()

        # Change to subdirectory
        with patch("pathlib.Path.cwd", return_value=subdir):
            root = get_project_root()
            assert root == project_dir

    def test_find_project_root_with_git(self, tmp_path):
        """Test finding project root by .git directory."""
        # Create directory structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        subdir = project_dir / "subdir"
        subdir.mkdir()

        # Create .git directory
        (project_dir / ".git").mkdir()

        # Change to subdirectory
        with patch("pathlib.Path.cwd", return_value=subdir):
            root = get_project_root()
            assert root == project_dir

    def test_fallback_to_cwd(self, tmp_path):
        """Test fallback to current directory when no marker found."""
        # Create directory without any markers
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=work_dir):
            root = get_project_root()
            assert root == work_dir


class TestLoadExperimentWithPathResolution:
    """Test load_experiment with path resolution."""

    def test_load_experiment_resolves_paths(self, tmp_path):
        """Test that load_experiment resolves relative paths."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create config file
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "ovmb_cache"},
            "openvino": {
                "mode": "build",
                "source_dir": "ovmb_cache/openvino_source",
                "toolchain": {"android_ndk": "ovmb_cache/android-sdk/ndk"},
            },
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "ovmb_cache/models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "artifacts/results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root to return our test directory
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            experiment = load_experiment(config_file)

            # Check resolved paths
            assert experiment.project.cache_dir == str(project_dir / "ovmb_cache")
            assert experiment.openvino.source_dir == str(
                project_dir / "ovmb_cache" / "openvino_source"
            )
            assert experiment.openvino.toolchain.android_ndk == str(
                project_dir / "ovmb_cache" / "android-sdk" / "ndk"
            )
            assert experiment.models[0].path == str(
                project_dir / "ovmb_cache" / "models" / "model1.xml"
            )
            assert experiment.report.sinks[0].path == str(
                project_dir / "artifacts" / "results.json"
            )

    def test_load_experiment_preserves_absolute_paths(self, tmp_path):
        """Test that load_experiment preserves absolute paths."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Use tmp_path for absolute paths to avoid permission issues
        abs_cache = tmp_path / "absolute" / "cache"
        abs_openvino = tmp_path / "absolute" / "openvino"
        abs_ndk = tmp_path / "absolute" / "android-ndk"
        abs_model = tmp_path / "absolute" / "model1.xml"
        abs_results = tmp_path / "absolute" / "results.json"

        # Create config file with absolute paths
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": str(abs_cache)},
            "openvino": {
                "mode": "build",
                "source_dir": str(abs_openvino),
                "toolchain": {"android_ndk": str(abs_ndk)},
            },
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": str(abs_model)}],
            "report": {"sinks": [{"type": "json", "path": str(abs_results)}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root to return our test directory
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            experiment = load_experiment(config_file)

            # Check that absolute paths are preserved
            assert experiment.project.cache_dir == str(abs_cache)
            assert experiment.openvino.source_dir == str(abs_openvino)
            assert experiment.openvino.toolchain.android_ndk == str(abs_ndk)
            assert experiment.models[0].path == str(abs_model)
            assert experiment.report.sinks[0].path == str(abs_results)

    def test_load_experiment_with_model_directories(self, tmp_path):
        """Test load_experiment with model directories format."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create model directories and files
        models_dir = project_dir / "ovmb_cache" / "models"
        models_dir.mkdir(parents=True)
        (models_dir / "model1.xml").touch()

        # Create config file with model directories
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "ovmb_cache"},
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": {
                "directories": ["ovmb_cache/models"],
                "extensions": [".xml"],
                "models": [{"name": "extra", "path": "ovmb_cache/extra.xml"}],
            },
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root to return our test directory
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            experiment = load_experiment(config_file)

            # Check resolved paths
            assert experiment.project.cache_dir == str(project_dir / "ovmb_cache")
            # Model paths should be resolved after directory scanning
            assert any(
                str(project_dir / "ovmb_cache" / "models" / "model1.xml") in m.path
                for m in experiment.models
            )


class TestIntegrationWithRealConfig:
    """Integration tests with real configuration files."""

    def test_android_example_config(self):
        """Test loading android_example.yaml with path resolution."""
        config_path = Path("experiments/android_example.yaml")
        if not config_path.exists():
            pytest.skip("android_example.yaml not found")

        experiment = load_experiment(config_path)

        # Check that paths are resolved (should be absolute)
        if experiment.project.cache_dir:
            assert Path(experiment.project.cache_dir).is_absolute()
        if experiment.openvino.source_dir:
            assert Path(experiment.openvino.source_dir).is_absolute()
        if experiment.openvino.toolchain.android_ndk:
            assert Path(experiment.openvino.toolchain.android_ndk).is_absolute()

    def test_e2e_config(self):
        """Test loading E2E test config with path resolution."""
        config_path = Path("experiments/android_example.yaml")
        if not config_path.exists():
            pytest.skip("E2E config not found")

        experiment = load_experiment(config_path)

        # Check that paths are resolved
        assert Path(experiment.project.cache_dir).is_absolute()

        # source_dir and android_ndk are auto-configured during load
        # They should be set to paths within cache_dir
        if experiment.openvino.source_dir:
            assert Path(experiment.openvino.source_dir).is_absolute()
            assert "ovmb_cache/openvino_source" in experiment.openvino.source_dir

        if experiment.openvino.toolchain.android_ndk:
            assert Path(experiment.openvino.toolchain.android_ndk).is_absolute()
            assert "ovmb_cache/android-sdk/ndk" in experiment.openvino.toolchain.android_ndk

        # Check cache_dir is always set
        assert "ovmb_cache" in experiment.project.cache_dir
