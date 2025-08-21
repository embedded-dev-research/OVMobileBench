"""Integration tests for cache_dir parameter in YAML configurations."""

import tempfile
from pathlib import Path

import yaml

from ovmobilebench.config.loader import load_experiment


class TestCacheDirYAMLIntegration:
    """Test cache_dir parameter loading from YAML files."""

    def test_load_android_example_yaml_with_cache_dir(self):
        """Test loading android_example.yaml with cache_dir parameter."""
        # Create temporary YAML with cache_dir
        android_config = {
            "project": {
                "name": "ovmobilebench-android",
                "run_id": "android_benchmark_001",
                "description": "OpenVINO benchmark on Android device",
                "cache_dir": "ovmb_cache",
            },
            "openvino": {"mode": "install", "install_dir": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["device1"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(android_config, f)
            yaml_path = Path(f.name)

        try:
            experiment = load_experiment(yaml_path)
            assert experiment.project.name == "ovmobilebench-android"
            assert experiment.project.run_id == "android_benchmark_001"
            assert experiment.project.description == "OpenVINO benchmark on Android device"
            assert experiment.project.cache_dir == "ovmb_cache"
        finally:
            yaml_path.unlink()

    def test_load_raspberry_pi_yaml_with_cache_dir(self):
        """Test loading raspberry pi configuration with cache_dir parameter."""
        rpi_config = {
            "project": {
                "name": "raspberry-pi-benchmark",
                "run_id": "rpi-perf-test",
                "description": "Performance benchmarking on Raspberry Pi with OpenVINO",
                "cache_dir": "ovmb_cache",
            },
            "openvino": {"mode": "build", "source_dir": "/path/to/openvino"},
            "device": {
                "kind": "linux_ssh",
                "host": "192.168.1.100",
                "username": "pi",
                "password": "raspberry",
            },
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(rpi_config, f)
            yaml_path = Path(f.name)

        try:
            experiment = load_experiment(yaml_path)
            assert experiment.project.name == "raspberry-pi-benchmark"
            assert experiment.project.run_id == "rpi-perf-test"
            assert (
                experiment.project.description
                == "Performance benchmarking on Raspberry Pi with OpenVINO"
            )
            assert experiment.project.cache_dir == "ovmb_cache"
        finally:
            yaml_path.unlink()

    def test_load_yaml_with_custom_cache_dir(self):
        """Test loading YAML with custom cache directory."""
        custom_config = {
            "project": {
                "name": "custom-experiment",
                "run_id": "custom-001",
                "description": "Custom cache directory test",
                "cache_dir": "/custom/path/to/cache",
            },
            "openvino": {"mode": "install", "install_dir": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["device1"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(custom_config, f)
            yaml_path = Path(f.name)

        try:
            experiment = load_experiment(yaml_path)
            assert experiment.project.cache_dir == "/custom/path/to/cache"
        finally:
            yaml_path.unlink()

    def test_load_yaml_without_cache_dir_uses_default(self):
        """Test loading YAML without cache_dir uses default value."""
        config_without_cache = {
            "project": {
                "name": "no-cache-experiment",
                "run_id": "no-cache-001",
                "description": "Test without cache_dir",
            },
            "openvino": {"mode": "install", "install_dir": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["device1"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_without_cache, f)
            yaml_path = Path(f.name)

        try:
            experiment = load_experiment(yaml_path)
            assert experiment.project.name == "no-cache-experiment"
            assert experiment.project.cache_dir == "ovmb_cache"  # Should use default
        finally:
            yaml_path.unlink()

    def test_load_e2e_config_with_cache_dir(self):
        """Test loading E2E configuration with cache_dir parameter."""
        e2e_config = {
            "project": {
                "name": "e2e-android-resnet50",
                "run_id": "test_001",
                "description": "E2E test for Android ResNet50 benchmarking",
                "cache_dir": "ovmb_cache",
            },
            "openvino": {"mode": "build", "source_dir": "/path/to/openvino"},
            "device": {"kind": "android", "serials": ["emulator-5554"]},
            "models": [{"name": "resnet-50", "path": "ovmb_cache/models/resnet-50-pytorch.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(e2e_config, f)
            yaml_path = Path(f.name)

        try:
            experiment = load_experiment(yaml_path)
            assert experiment.project.name == "e2e-android-resnet50"
            assert experiment.project.run_id == "test_001"
            assert experiment.project.description == "E2E test for Android ResNet50 benchmarking"
            assert experiment.project.cache_dir == "ovmb_cache"
        finally:
            yaml_path.unlink()

    def test_yaml_cache_dir_validation(self):
        """Test that cache_dir parameter is properly validated."""
        # Test with valid cache_dir
        valid_config = {
            "project": {
                "name": "valid-experiment",
                "run_id": "valid-001",
                "cache_dir": "valid_cache_dir",
            },
            "openvino": {"mode": "install", "install_dir": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["device1"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(valid_config, f)
            yaml_path = Path(f.name)

        try:
            experiment = load_experiment(yaml_path)
            assert experiment.project.cache_dir == "valid_cache_dir"
            # Verify it's a string type
            assert isinstance(experiment.project.cache_dir, str)
        finally:
            yaml_path.unlink()

    def test_load_actual_config_files(self):
        """Test loading actual configuration files from the repository."""
        import yaml

        # Test android_example.yaml - just verify cache_dir in raw YAML
        android_path = Path("experiments/android_example.yaml")
        if android_path.exists():
            with open(android_path) as f:
                android_data = yaml.safe_load(f)
            assert "cache_dir" in android_data["project"]
            assert android_data["project"]["cache_dir"] == "ovmb_cache"

        # Test raspberry_pi_example.yaml - just verify cache_dir in raw YAML
        rpi_path = Path("experiments/raspberry_pi_example.yaml")
        if rpi_path.exists():
            with open(rpi_path) as f:
                rpi_data = yaml.safe_load(f)
            assert "cache_dir" in rpi_data["project"]
            assert rpi_data["project"]["cache_dir"] == "ovmb_cache"

        # Test e2e config - just verify cache_dir in raw YAML
        e2e_path = Path("tests/e2e/configs/android_resnet50.yaml")
        if e2e_path.exists():
            with open(e2e_path) as f:
                e2e_data = yaml.safe_load(f)
            assert "cache_dir" in e2e_data["project"]
            assert e2e_data["project"]["cache_dir"] == "ovmb_cache"
