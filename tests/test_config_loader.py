"""Tests for configuration loader module."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
from pydantic import ValidationError

from ovmobilebench.config.loader import load_yaml, load_experiment, save_experiment
from ovmobilebench.config.schema import Experiment


class TestLoadYaml:
    """Test load_yaml function."""

    def test_load_yaml_file_not_found(self):
        """Test loading non-existent YAML file."""
        path = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError) as exc_info:
            load_yaml(path)
        # Use path.as_posix() for consistent forward slashes in error message
        assert f"Configuration file not found: {path.as_posix()}" in str(exc_info.value)

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_yaml_success(self, mock_yaml_load, mock_file, mock_exists):
        """Test successful YAML loading."""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"key": "value"}

        path = Path("/test/config.yaml")
        result = load_yaml(path)

        assert result == {"key": "value"}
        mock_file.assert_called_once_with(path, "r")
        mock_yaml_load.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content")
    def test_load_yaml_invalid_yaml(self, mock_file, mock_exists):
        """Test loading invalid YAML content."""
        mock_exists.return_value = True

        path = Path("/test/invalid.yaml")
        # yaml.safe_load should be able to handle this, but let's test yaml parsing error
        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
            with pytest.raises(yaml.YAMLError):
                load_yaml(path)

    @patch("pathlib.Path.exists")
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_load_yaml_io_error(self, mock_file, mock_exists):
        """Test IOError when opening file."""
        mock_exists.return_value = True

        path = Path("/test/config.yaml")
        with pytest.raises(IOError):
            load_yaml(path)


class TestLoadExperiment:
    """Test load_experiment function."""

    def test_load_experiment_with_string_path(self):
        """Test loading experiment with string path."""
        valid_config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with patch("ovmobilebench.config.loader.load_yaml", return_value=valid_config):
            result = load_experiment("/test/config.yaml")
            assert isinstance(result, Experiment)
            assert result.project.name == "test"

    def test_load_experiment_with_path_object(self):
        """Test loading experiment with Path object."""
        valid_config = {
            "project": {"name": "test", "run_id": "test_001"},
            "build": {"enabled": False, "openvino_repo": "/path/to/ov"},
            "device": {"kind": "android", "serials": ["test_device"]},
            "models": [{"name": "model1", "path": "model1.xml"}],
            "report": {"sinks": [{"type": "json", "path": "results.json"}]},
        }

        with patch("ovmobilebench.config.loader.load_yaml", return_value=valid_config):
            result = load_experiment(Path("/test/config.yaml"))
            assert isinstance(result, Experiment)
            assert result.project.name == "test"

    def test_load_experiment_invalid_config(self):
        """Test loading experiment with invalid configuration."""
        invalid_config = {"invalid": "config"}

        with patch("ovmobilebench.config.loader.load_yaml", return_value=invalid_config):
            with pytest.raises(ValidationError):
                load_experiment("/test/config.yaml")

    def test_load_experiment_file_not_found(self):
        """Test loading experiment when file doesn't exist."""
        with patch(
            "ovmobilebench.config.loader.load_yaml", side_effect=FileNotFoundError("File not found")
        ):
            with pytest.raises(FileNotFoundError):
                load_experiment("/nonexistent/config.yaml")


class TestSaveExperiment:
    """Test save_experiment function."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_dump")
    def test_save_experiment_success(self, mock_yaml_dump, mock_file):
        """Test successful experiment saving."""
        # Create a mock experiment
        experiment = MagicMock(spec=Experiment)
        experiment.model_dump.return_value = {"test": "config"}

        path = Path("/test/output.yaml")
        save_experiment(experiment, path)

        mock_file.assert_called_once_with(path, "w")
        experiment.model_dump.assert_called_once()
        mock_yaml_dump.assert_called_once_with(
            {"test": "config"},
            mock_file.return_value.__enter__.return_value,
            default_flow_style=False,
            sort_keys=False,
        )

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_save_experiment_io_error(self, mock_file):
        """Test IOError when saving experiment."""
        experiment = MagicMock(spec=Experiment)
        experiment.model_dump.return_value = {"test": "config"}

        path = Path("/test/output.yaml")
        with pytest.raises(IOError):
            save_experiment(experiment, path)

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_dump", side_effect=yaml.YAMLError("YAML error"))
    def test_save_experiment_yaml_error(self, mock_yaml_dump, mock_file):
        """Test YAML error when saving experiment."""
        experiment = MagicMock(spec=Experiment)
        experiment.model_dump.return_value = {"test": "config"}

        path = Path("/test/output.yaml")
        with pytest.raises(yaml.YAMLError):
            save_experiment(experiment, path)
