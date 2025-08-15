"""Tests for configuration module."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from ovbench.config.schema import (
    Experiment,
    BuildConfig,
    DeviceConfig,
    ModelItem,
    RunConfig,
    ReportConfig,
    ProjectConfig,
    SinkItem,
)


class TestModelItem:
    """Test ModelItem configuration."""
    
    def test_valid_model(self):
        """Test creating valid model configuration."""
        model = ModelItem(
            name="resnet50",
            path="models/resnet50.xml",
            precision="FP16",
            tags={"framework": "tensorflow"}
        )
        assert model.name == "resnet50"
        assert model.path == "models/resnet50.xml"
        assert model.precision == "FP16"
        assert model.tags["framework"] == "tensorflow"
    
    def test_invalid_model_path(self):
        """Test model with invalid path (not XML)."""
        with pytest.raises(ValidationError) as exc_info:
            ModelItem(
                name="resnet50",
                path="models/resnet50.bin"  # Should be .xml
            )
        assert "Model path must be an XML file" in str(exc_info.value)


class TestDeviceConfig:
    """Test DeviceConfig validation."""
    
    def test_android_device_valid(self):
        """Test valid Android device configuration."""
        device = DeviceConfig(
            kind="android",
            serials=["12345678"],
            push_dir="/data/local/tmp/ovbench"
        )
        assert device.kind == "android"
        assert device.serials == ["12345678"]
    
    def test_android_device_no_serial(self):
        """Test Android device without serial."""
        with pytest.raises(ValidationError) as exc_info:
            DeviceConfig(
                kind="android",
                serials=[]  # Empty serials for Android
            )
        assert "Android device requires at least one serial" in str(exc_info.value)
    
    def test_linux_ssh_device(self):
        """Test Linux SSH device configuration."""
        device = DeviceConfig(
            kind="linux_ssh",
            host="192.168.1.100",
            user="pi",
            key_path="/home/user/.ssh/id_rsa"
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
            }
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
        assert combo['model_name'] == "model1"
        assert combo['model_xml'] == "model1.xml"
        assert 'device' in combo
        assert 'api' in combo
        assert 'niter' in combo
    
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
            }
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