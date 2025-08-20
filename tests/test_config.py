"""Tests for configuration module."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from ovmobilebench.config.loader import load_experiment, scan_model_directories
from ovmobilebench.config.schema import DeviceConfig, Experiment, ModelItem, ModelsConfig


class TestModelItem:
    """Test ModelItem configuration."""

    def test_valid_model(self):
        """Test creating valid model configuration."""
        model = ModelItem(
            name="resnet50",
            path="models/resnet50.xml",
            precision="FP16",
            tags={"framework": "tensorflow"},
        )
        assert model.name == "resnet50"
        assert model.path == "models/resnet50.xml"
        assert model.precision == "FP16"
        assert model.tags["framework"] == "tensorflow"

    def test_invalid_model_path(self):
        """Test model with invalid path (not XML)."""
        with pytest.raises(ValidationError) as exc_info:
            ModelItem(name="resnet50", path="models/resnet50.bin")  # Should be .xml
        assert "Model path must be an XML file" in str(exc_info.value)


class TestDeviceConfig:
    """Test DeviceConfig validation."""

    def test_android_device_valid(self):
        """Test valid Android device configuration."""
        device = DeviceConfig(
            kind="android", serials=["12345678"], push_dir="/data/local/tmp/ovmobilebench"
        )
        assert device.kind == "android"
        assert device.serials == ["12345678"]

    def test_android_device_no_serial(self):
        """Test Android device without serial - should be allowed for auto-detect."""
        device = DeviceConfig(kind="android", serials=[])
        assert device.kind == "android"
        assert device.serials == []  # Empty serials allowed for auto-detect

    def test_linux_ssh_device(self):
        """Test Linux SSH device configuration."""
        device = DeviceConfig(
            kind="linux_ssh", host="192.168.1.100", user="pi", key_path="/home/user/.ssh/id_rsa"
        )
        assert device.kind == "linux_ssh"
        assert device.host == "192.168.1.100"


class TestExperiment:
    """Test complete Experiment configuration."""

    @pytest.fixture
    def minimal_config(self):
        """Create minimal valid configuration."""
        return {
            "project": {
                "name": "test",
                "run_id": "test_001",
            },
            "build": {
                "enabled": False,
                "openvino_repo": "/path/to/ov",
            },
            "device": {
                "kind": "android",
                "serials": ["test_device"],
            },
            "models": [
                {
                    "name": "model1",
                    "path": "model1.xml",
                }
            ],
            "report": {
                "sinks": [
                    {
                        "type": "json",
                        "path": "results.json",
                    }
                ]
            },
        }

    def test_create_experiment(self, minimal_config):
        """Test creating experiment from config."""
        exp = Experiment(**minimal_config)
        assert exp.project.name == "test"
        assert exp.project.run_id == "test_001"
        assert len(exp.models) == 1
        assert exp.models[0].name == "model1"

    def test_expand_matrix_for_model(self, minimal_config):
        """Test expanding run matrix for model."""
        exp = Experiment(**minimal_config)
        model = exp.models[0]

        # Use default matrix
        combos = exp.expand_matrix_for_model(model)

        assert len(combos) > 0
        combo = combos[0]
        assert combo["model_name"] == "model1"
        assert combo["model_xml"] == "model1.xml"
        assert "device" in combo
        assert "api" in combo
        assert "niter" in combo

    def test_get_total_runs(self, minimal_config):
        """Test calculating total number of runs."""
        # Add custom matrix
        minimal_config["run"] = {
            "repeats": 3,
            "matrix": {
                "device": ["CPU"],
                "api": ["sync"],
                "niter": [100, 200],
                "nireq": [1],
                "nstreams": ["1"],
                "threads": [2, 4],
                "infer_precision": ["FP16"],
            },
        }

        exp = Experiment(**minimal_config)

        # 1 model * 2 niter * 2 threads * 3 repeats * 1 device = 12
        total = exp.get_total_runs()
        assert total == 12

    def test_invalid_sink_type(self, minimal_config):
        """Test invalid sink type."""
        minimal_config["report"]["sinks"][0]["type"] = "invalid"

        with pytest.raises(ValidationError):
            Experiment(**minimal_config)


class TestModelsConfig:
    """Test ModelsConfig schema."""

    def test_valid_directories_config(self):
        """Test valid ModelsConfig with directories."""
        config = ModelsConfig(
            directories=["/path/to/models"],
            extensions=[".xml", ".onnx"],
        )
        assert config.directories == ["/path/to/models"]
        assert ".xml" in config.extensions
        assert ".onnx" in config.extensions

    def test_valid_models_config(self):
        """Test valid ModelsConfig with explicit models."""
        model = ModelItem(name="test", path="test.xml")
        config = ModelsConfig(models=[model])
        assert len(config.models) == 1
        assert config.models[0].name == "test"

    def test_mixed_config(self):
        """Test ModelsConfig with both directories and models."""
        model = ModelItem(name="test", path="test.xml")
        config = ModelsConfig(
            directories=["/path/to/models"],
            extensions=[".xml"],
            models=[model],
        )
        assert config.directories == ["/path/to/models"]
        assert len(config.models) == 1

    def test_empty_config_fails(self):
        """Test ModelsConfig fails when both directories and models are empty."""
        with pytest.raises(ValidationError) as exc_info:
            ModelsConfig()
        assert "Either 'directories' or 'models' must be specified" in str(exc_info.value)

    def test_default_extensions(self):
        """Test default extensions are set."""
        config = ModelsConfig(directories=["/path/to/models"])
        assert ".xml" in config.extensions
        assert ".onnx" in config.extensions
        assert ".pb" in config.extensions
        assert ".tflite" in config.extensions
        assert ".bin" in config.extensions


class TestModelDirectoryScanning:
    """Test model directory scanning functionality."""

    def test_scan_empty_directories(self):
        """Test scanning empty directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)
            assert len(models) == 0

    def test_scan_with_models(self):
        """Test scanning directories with model files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test model files
            (temp_path / "resnet50_fp16.xml").touch()
            (temp_path / "yolo_fp32.xml").touch()
            (temp_path / "bert_int8.xml").touch()
            (temp_path / "other.onnx").touch()  # Will be ignored (not .xml)

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)

            assert len(models) == 3
            model_names = [m.name for m in models]
            assert "resnet50_fp16" in model_names
            assert "yolo_fp32" in model_names
            assert "bert_int8" in model_names

    def test_precision_inference(self):
        """Test precision inference from filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files with precision indicators
            (temp_path / "model_fp16.xml").touch()
            (temp_path / "model_fp32.xml").touch()
            (temp_path / "model_int8.xml").touch()
            (temp_path / "model_unknown.xml").touch()

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)

            precision_map = {m.name: m.precision for m in models}
            assert precision_map["model_fp16"] == "FP16"
            assert precision_map["model_fp32"] == "FP32"
            assert precision_map["model_int8"] == "INT8"
            assert precision_map["model_unknown"] is None

    def test_scan_with_explicit_models(self):
        """Test scanning with both explicit models and directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "discovered.xml").touch()

            explicit_model = ModelItem(name="explicit", path="explicit.xml")
            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
                models=[explicit_model],
            )
            models = scan_model_directories(config)

            # Should have both explicit and discovered models
            assert len(models) == 2
            model_names = [m.name for m in models]
            assert "explicit" in model_names
            assert "discovered" in model_names

    def test_scan_nonexistent_directory(self):
        """Test scanning nonexistent directory."""
        config = ModelsConfig(
            directories=["/nonexistent/path"],
            extensions=[".xml"],
        )
        models = scan_model_directories(config)
        assert len(models) == 0

    def test_recursive_scanning(self):
        """Test recursive directory scanning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested directory structure
            subdir = temp_path / "subdir"
            subdir.mkdir()

            (temp_path / "root_model.xml").touch()
            (subdir / "sub_model.xml").touch()

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)

            assert len(models) == 2
            model_names = [m.name for m in models]
            assert "root_model" in model_names
            assert "sub_model" in model_names

    def test_metadata_tags(self):
        """Test that discovered models have correct metadata tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test_model.xml").touch()

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)

            assert len(models) == 1
            model = models[0]
            assert model.tags["source"] == "directory_scan"
            assert model.tags["directory"] == temp_dir

    def test_scan_duplicate_model_skip(self):
        """Test that models already in explicit list are skipped during scanning."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            model_path = temp_path / "duplicate.xml"
            model_path.touch()

            # Create explicit model with same path as discovered one
            explicit_model = ModelItem(name="explicit_duplicate", path=str(model_path))
            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
                models=[explicit_model],
            )
            models = scan_model_directories(config)

            # Should only have the explicit model, not a duplicate from scanning
            assert len(models) == 1
            assert models[0].name == "explicit_duplicate"

    def test_scan_multiple_extensions(self):
        """Test scanning with multiple file extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different extensions
            (temp_path / "model1.xml").touch()
            (temp_path / "model2.onnx").touch()
            (temp_path / "model3.pb").touch()
            (temp_path / "ignored.txt").touch()  # Should be ignored

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml", ".onnx", ".pb"],
            )
            models = scan_model_directories(config)

            # Only .xml files are actually added (see loader.py line 56)
            assert len(models) == 1
            assert models[0].name == "model1"

    def test_scan_precision_variations(self):
        """Test precision inference with different naming patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with various precision naming patterns
            (temp_path / "model_F16.xml").touch()
            (temp_path / "model_f32.xml").touch()
            (temp_path / "model_I8.xml").touch()

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)

            precision_map = {m.name: m.precision for m in models}
            assert precision_map["model_F16"] == "FP16"
            assert precision_map["model_f32"] == "FP32"
            assert precision_map["model_I8"] == "INT8"


class TestExperimentWithModelsConfig:
    """Test Experiment with new ModelsConfig format."""

    @pytest.fixture
    def models_config_experiment(self):
        """Create experiment config with ModelsConfig format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "test_model.xml").touch()

            config = {
                "project": {
                    "name": "test",
                    "run_id": "test_001",
                },
                "build": {
                    "enabled": False,
                    "openvino_repo": "/path/to/ov",
                },
                "device": {
                    "kind": "android",
                    "serials": ["test_device"],
                },
                "models": {
                    "directories": [temp_dir],
                    "extensions": [".xml"],
                },
                "report": {"sinks": [{"type": "json", "path": "results.json"}]},
            }
            yield config, temp_dir

    def test_get_model_list_with_new_format(self, models_config_experiment):
        """Test get_model_list with ModelsConfig format."""
        config_dict, _ = models_config_experiment

        # Create experiment via loader to process directory scanning
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_dict, f)
            temp_config_path = f.name

        try:
            exp = load_experiment(temp_config_path)
            models = exp.get_model_list()
            assert len(models) == 1
            assert models[0].name == "test_model"
        finally:
            Path(temp_config_path).unlink()

    def test_backward_compatibility(self):
        """Test that old list format still works."""
        config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": [{"name": "old_model", "path": "old_model.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        exp = Experiment(**config)
        models = exp.get_model_list()
        assert len(models) == 1
        assert models[0].name == "old_model"

    def test_mixed_configuration_loading(self):
        """Test loading configuration with both directories and explicit models."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "discovered.xml").touch()

            config = {
                "project": {"name": "test", "run_id": "test_001"},
                "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
                "device": {"kind": "android", "serials": ["test_device"]},
                "models": {
                    "directories": [temp_dir],
                    "extensions": [".xml"],
                    "models": [{"name": "explicit", "path": "explicit.xml"}],
                },
                "report": {"sinks": [{"type": "json", "path": "results.json"}]},
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                import yaml

                yaml.dump(config, f)
                temp_config_path = f.name

            try:
                exp = load_experiment(temp_config_path)
                models = exp.get_model_list()
                assert len(models) == 2
                model_names = [m.name for m in models]
                assert "explicit" in model_names
                assert "discovered" in model_names
            finally:
                Path(temp_config_path).unlink()

    def test_get_model_list_with_models_config_object(self):
        """Test get_model_list when models is ModelsConfig object."""
        # Create ModelsConfig directly
        explicit_model = ModelItem(name="explicit", path="explicit.xml")
        models_config = ModelsConfig(models=[explicit_model])

        config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": models_config,
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        exp = Experiment(**config)
        models = exp.get_model_list()
        assert len(models) == 1
        assert models[0].name == "explicit"

    def test_get_model_list_with_empty_models_config(self):
        """Test get_model_list when ModelsConfig has no models."""
        models_config = ModelsConfig(directories=["/nonexistent"])

        config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": models_config,
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        exp = Experiment(**config)
        models = exp.get_model_list()
        assert len(models) == 0

    def test_get_model_list_with_invalid_type(self):
        """Test get_model_list when models is neither list nor ModelsConfig."""
        # Create a minimal experiment and manually set models to invalid type
        config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": [{"name": "temp", "path": "temp.xml"}],  # Valid for creation
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        exp = Experiment(**config)
        # Manually set to invalid type to test fallback
        object.__setattr__(exp, "models", "invalid")
        models = exp.get_model_list()
        assert len(models) == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_models_config_with_only_directories_no_models(self):
        """Test ModelsConfig with directories but no explicit models."""
        config = ModelsConfig(directories=["/path"])
        assert config.directories == ["/path"]
        assert config.models is None

    def test_models_config_with_only_models_no_directories(self):
        """Test ModelsConfig with models but no directories."""
        model = ModelItem(name="test", path="test.xml")
        config = ModelsConfig(models=[model])
        assert config.models == [model]
        assert config.directories is None

    def test_scan_with_no_models_in_config(self):
        """Test scan_model_directories when models is None."""
        config = ModelsConfig(directories=["/nonexistent"])
        models = scan_model_directories(config)
        assert len(models) == 0

    def test_scan_with_no_directories_in_config(self):
        """Test scan_model_directories when directories is None."""
        model = ModelItem(name="test", path="test.xml")
        config = ModelsConfig(models=[model])
        models = scan_model_directories(config)
        assert len(models) == 1
        assert models[0].name == "test"

    def test_precision_inference_case_variations(self):
        """Test precision inference with various case combinations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test various case combinations
            (temp_path / "model_FP16.xml").touch()
            (temp_path / "model_Fp32.xml").touch()
            (temp_path / "model_INT8.xml").touch()
            (temp_path / "model_i8.xml").touch()  # lowercase i8

            config = ModelsConfig(
                directories=[temp_dir],
                extensions=[".xml"],
            )
            models = scan_model_directories(config)

            precision_map = {m.name: m.precision for m in models}
            assert precision_map["model_FP16"] == "FP16"
            assert precision_map["model_Fp32"] == "FP32"
            assert precision_map["model_INT8"] == "INT8"
            assert precision_map["model_i8"] == "INT8"

    def test_experiment_with_complex_models_config_dict(self):
        """Test Experiment creation with complex ModelsConfig dict."""
        config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": {
                "directories": ["/path1", "/path2"],
                "extensions": [".xml", ".onnx", ".pb"],
                "models": [
                    {"name": "explicit1", "path": "explicit1.xml"},
                    {"name": "explicit2", "path": "explicit2.xml"},
                ],
            },
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        # This will be processed by load_experiment, not directly by Experiment
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config, f)
            temp_config_path = f.name

        try:
            exp = load_experiment(temp_config_path)
            # Should be converted to list format
            assert isinstance(exp.models, list)
            # Should have at least the explicit models
            model_names = [m.name if hasattr(m, "name") else m["name"] for m in exp.models]
            assert "explicit1" in model_names
            assert "explicit2" in model_names
        finally:
            Path(temp_config_path).unlink()

    def test_device_config_backward_compatibility_fields(self):
        """Test DeviceConfig field compatibility (kind vs type, user vs username, etc)."""
        # Test kind vs type
        config1 = DeviceConfig(type="android", serials=["test"])
        assert config1.kind == "android"
        assert config1.type == "android"

        # Test user vs username
        config2 = DeviceConfig(kind="linux_ssh", host="test", user="testuser")
        assert config2.username == "testuser"
        assert config2.user == "testuser"

        # Test key_path vs key_filename
        config3 = DeviceConfig(kind="linux_ssh", host="test", key_path="/path/to/key")
        assert config3.key_filename == "/path/to/key"
        assert config3.key_path == "/path/to/key"

    def test_experiment_total_runs_with_no_devices(self):
        """Test get_total_runs when device serials is empty."""
        config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": []},  # Empty serials
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        exp = Experiment(**config)
        total = exp.get_total_runs()
        # Should default to 1 device when serials is empty
        assert total >= 1
