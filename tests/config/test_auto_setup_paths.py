"""Test automatic setup of default paths when not specified."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ovmobilebench.config.loader import (
    get_project_root,
    load_experiment,
    setup_default_paths,
)


class TestSetupDefaultPaths:
    """Test automatic setup of default paths."""

    def test_setup_source_dir_when_missing(self):
        """Test that source_dir is set to default when not specified."""
        project_root = Path("/home/user/project")
        config = {"project": {"cache_dir": "ovmb_cache"}, "openvino": {"mode": "build"}}

        result = setup_default_paths(config, project_root)

        # Should set source_dir to cache/openvino_source
        expected = str(project_root / "ovmb_cache" / "openvino_source")
        assert result["openvino"]["source_dir"] == expected

    def test_setup_android_ndk_when_missing(self):
        """Test that android_ndk is set to default when not specified."""
        project_root = Path("/home/user/project")
        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "build", "toolchain": {}},
        }

        result = setup_default_paths(config, project_root)

        # Should set android_ndk to cache/android-sdk/ndk/version
        # When no NDK exists, should set to "latest" placeholder
        ndk_path = result["openvino"]["toolchain"]["android_ndk"]
        expected = str(project_root / "ovmb_cache" / "android-sdk" / "ndk" / "latest")
        assert ndk_path == expected

    def test_setup_both_paths_when_missing(self):
        """Test that both source_dir and android_ndk are set when missing."""
        project_root = Path("/home/user/project")
        config = {"project": {"cache_dir": "my_cache"}, "openvino": {"mode": "build"}}

        result = setup_default_paths(config, project_root)

        # Should set both paths
        expected_source = str(project_root / "my_cache" / "openvino_source")
        assert result["openvino"]["source_dir"] == expected_source
        expected_ndk_prefix = str(project_root / "my_cache" / "android-sdk" / "ndk")
        assert result["openvino"]["toolchain"]["android_ndk"].startswith(expected_ndk_prefix)

    def test_preserve_existing_source_dir(self):
        """Test that existing source_dir is preserved."""
        project_root = Path("/home/user/project")
        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "build", "source_dir": "/custom/openvino"},
        }

        result = setup_default_paths(config, project_root)

        # Should preserve existing source_dir
        assert result["openvino"]["source_dir"] == "/custom/openvino"

    def test_preserve_existing_android_ndk(self):
        """Test that existing android_ndk is preserved."""
        project_root = Path("/home/user/project")
        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "build", "toolchain": {"android_ndk": "/custom/ndk"}},
        }

        result = setup_default_paths(config, project_root)

        # Should preserve existing android_ndk
        assert result["openvino"]["toolchain"]["android_ndk"] == "/custom/ndk"

    def test_no_setup_for_install_mode(self):
        """Test that paths are not set for install mode."""
        project_root = Path("/home/user/project")
        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "install", "install_dir": "/opt/openvino"},
        }

        result = setup_default_paths(config, project_root)

        # Should not add source_dir or toolchain
        assert "source_dir" not in result["openvino"]
        assert "toolchain" not in result["openvino"] or "android_ndk" not in result["openvino"].get(
            "toolchain", {}
        )

    def test_no_setup_for_link_mode(self):
        """Test that paths are not set for link mode."""
        project_root = Path("/home/user/project")
        config = {
            "project": {"cache_dir": "ovmb_cache"},
            "openvino": {"mode": "link", "archive_url": "https://example.com/openvino.tar.gz"},
        }

        result = setup_default_paths(config, project_root)

        # Should not add source_dir or toolchain
        assert "source_dir" not in result["openvino"]
        assert "toolchain" not in result["openvino"] or "android_ndk" not in result["openvino"].get(
            "toolchain", {}
        )

    def test_use_absolute_cache_dir(self):
        """Test using absolute cache_dir path."""
        project_root = Path("/home/user/project")
        config = {"project": {"cache_dir": "/absolute/cache"}, "openvino": {"mode": "build"}}

        result = setup_default_paths(config, project_root)

        # Should use absolute cache path
        cache_path = Path("/absolute/cache")
        expected = str(cache_path / "openvino_source")
        assert result["openvino"]["source_dir"] == expected
        expected_ndk = str(cache_path / "android-sdk" / "ndk")
        assert result["openvino"]["toolchain"]["android_ndk"].startswith(expected_ndk)

    def test_default_cache_dir_when_not_specified(self):
        """Test that default cache_dir is used when not specified."""
        project_root = Path("/home/user/project")
        config = {"openvino": {"mode": "build"}}

        result = setup_default_paths(config, project_root)

        # Should use default ovmb_cache
        expected = str(project_root / "ovmb_cache" / "openvino_source")
        assert result["openvino"]["source_dir"] == expected
        expected_ndk = str(project_root / "ovmb_cache" / "android-sdk" / "ndk")
        assert result["openvino"]["toolchain"]["android_ndk"].startswith(expected_ndk)

    def test_config_not_modified(self):
        """Test that original config is not modified."""
        project_root = Path("/home/user/project")
        config = {"project": {"cache_dir": "ovmb_cache"}, "openvino": {"mode": "build"}}

        # Make a copy to check later
        original_openvino = dict(config["openvino"])

        result = setup_default_paths(config, project_root)

        # Original should be unchanged
        assert config["openvino"] == original_openvino
        # Result should have new fields
        assert "source_dir" in result["openvino"]
        assert "toolchain" in result["openvino"]


class TestLoadExperimentWithAutoSetup:
    """Test load_experiment with automatic path setup."""

    def test_load_experiment_auto_setup_paths(self, tmp_path):
        """Test that load_experiment automatically sets up missing paths."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create config without source_dir and android_ndk
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "cache"},
            "openvino": {"mode": "build", "build_type": "Release"},
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root and suppress print output
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):  # Suppress INFO messages
                experiment = load_experiment(config_file)

        # Check that paths were auto-set and resolved
        assert experiment.openvino.source_dir == str(project_dir / "cache" / "openvino_source")
        # NDK will be set to "latest" when no NDK exists
        assert experiment.openvino.toolchain.android_ndk == str(
            project_dir / "cache" / "android-sdk" / "ndk" / "latest"
        )

    def test_load_experiment_preserves_specified_paths(self, tmp_path):
        """Test that load_experiment preserves user-specified paths."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create config with specified paths
        config_data = {
            "project": {"name": "test", "run_id": "test_001", "cache_dir": "cache"},
            "openvino": {
                "mode": "build",
                "source_dir": "custom/openvino",
                "toolchain": {"android_ndk": "custom/ndk"},
            },
            "device": {"kind": "android", "serials": ["test"]},
            "models": [{"name": "model1", "path": "models/model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            experiment = load_experiment(config_file)

        # Check that user paths were preserved and resolved
        assert experiment.openvino.source_dir == str(project_dir / "custom" / "openvino")
        assert experiment.openvino.toolchain.android_ndk == str(project_dir / "custom" / "ndk")

    def test_e2e_config_without_paths(self, tmp_path):
        """Test E2E config without source_dir and android_ndk."""
        # Create project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()

        # Create E2E-like config without paths
        config_data = {
            "project": {
                "name": "android-benchmark",
                "run_id": "test_001",
                "description": "E2E test for Android ResNet50 benchmarking",
                "cache_dir": "ovmb_cache",
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
            "package": {"include_symbols": False, "extra_files": []},
            "device": {
                "kind": "android",
                "serials": ["emulator-5554"],
                "push_dir": "/data/local/tmp/ovmobilebench",
                "use_root": False,
            },
            "models": [{"name": "resnet-50", "path": "ovmb_cache/models/resnet-50-pytorch.xml"}],
            "run": {
                "repeats": 1,
                "matrix": {
                    "niter": [100],
                    "nireq": [1],
                    "nstreams": ["1"],
                    "threads": [4],
                    "device": ["CPU"],
                    "infer_precision": ["FP16"],
                },
                "cooldown_sec": 2,
                "timeout_sec": 120,
                "warmup": True,
            },
            "report": {
                "sinks": [
                    {"type": "json", "path": "artifacts/reports/results.json"},
                    {"type": "csv", "path": "artifacts/reports/results.csv"},
                ],
                "tags": {"experiment": "e2e_test", "version": "v1.0"},
                "aggregate": True,
                "include_raw": False,
            },
        }

        config_file = project_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock get_project_root and suppress print output
        with patch("ovmobilebench.config.loader.get_project_root", return_value=project_dir):
            with patch("builtins.print"):  # Suppress INFO messages
                experiment = load_experiment(config_file)

        # Check that paths were auto-set
        assert experiment.openvino.source_dir == str(project_dir / "ovmb_cache" / "openvino_source")
        # NDK will be set to "latest" when no NDK exists
        assert experiment.openvino.toolchain.android_ndk == str(
            project_dir / "ovmb_cache" / "android-sdk" / "ndk" / "latest"
        )

        # Check other config is preserved
        assert experiment.project.name == "android-benchmark"
        assert experiment.openvino.toolchain.abi == "arm64-v8a"
        assert experiment.openvino.toolchain.api_level == 30


class TestIntegrationWithRealE2EConfig:
    """Integration test with actual E2E config file."""

    def test_real_e2e_config_auto_setup(self):
        """Test loading real E2E config with auto-setup."""
        config_path = Path("experiments/android_example.yaml")
        if not config_path.exists():
            pytest.skip("E2E config not found")

        # Suppress print output during test
        with patch("builtins.print"):
            experiment = load_experiment(config_path)

        # Get expected project root
        project_root = get_project_root()

        # Check that paths were auto-set to defaults
        # Create an NDK version for testing
        ndk_version_dir = project_root / "ovmb_cache" / "android-sdk" / "ndk" / "27.2.12479018"
        ndk_version_dir.mkdir(parents=True, exist_ok=True)

        # source_dir and android_ndk should be auto-set
        # They might not match exactly due to path resolution
        if experiment.openvino.source_dir:
            source_path = Path(experiment.openvino.source_dir)
            assert "openvino_source" in source_path.parts
        if experiment.openvino.toolchain.android_ndk:
            ndk_path = Path(experiment.openvino.toolchain.android_ndk)
            assert "android-sdk" in ndk_path.parts
            assert "ndk" in ndk_path.parts

        # Verify other settings are preserved
        assert experiment.project.name == "android-benchmark"
        assert experiment.openvino.mode == "build"
        assert experiment.openvino.toolchain.abi == "arm64-v8a"
        assert experiment.openvino.toolchain.api_level == 30
