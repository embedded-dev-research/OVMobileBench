"""Tests for report sink module."""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from ovmobilebench.report.sink import CSVSink, JSONSink, ReportSink


class TestReportSink:
    """Test abstract ReportSink base class."""

    def test_abstract_base_class(self):
        """Test that ReportSink cannot be instantiated."""
        with pytest.raises(TypeError):
            ReportSink()

    def test_abstract_method(self):
        """Test that write method is abstract."""

        class IncompleteReportSink(ReportSink):
            pass

        with pytest.raises(TypeError):
            IncompleteReportSink()


class TestJSONSink:
    """Test JSONSink implementation."""

    @patch("ovmobilebench.report.sink.atomic_write")
    @patch("ovmobilebench.report.sink.ensure_dir")
    def test_write_json_simple_data(self, mock_ensure_dir, mock_atomic_write):
        """Test writing simple JSON data."""
        sink = JSONSink()
        data = [{"name": "test", "value": 123}]
        path = Path("/test/output.json")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        expected_content = json.dumps(data, indent=2, default=str)
        mock_atomic_write.assert_called_once_with(path, expected_content)

    @patch("ovmobilebench.report.sink.atomic_write")
    @patch("ovmobilebench.report.sink.ensure_dir")
    def test_write_json_complex_data(self, mock_ensure_dir, mock_atomic_write):
        """Test writing complex JSON data with nested objects."""
        sink = JSONSink()
        data = [
            {
                "experiment": "test",
                "results": {
                    "throughput": 123.45,
                    "latency": {"min": 1.0, "max": 5.0},
                },
                "metadata": {"tags": ["tag1", "tag2"]},
            }
        ]
        path = Path("/test/complex.json")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        expected_content = json.dumps(data, indent=2, default=str)
        mock_atomic_write.assert_called_once_with(path, expected_content)

    @patch("ovmobilebench.report.sink.atomic_write")
    @patch("ovmobilebench.report.sink.ensure_dir")
    def test_write_json_empty_data(self, mock_ensure_dir, mock_atomic_write):
        """Test writing empty JSON data."""
        sink = JSONSink()
        data = []
        path = Path("/test/empty.json")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        expected_content = json.dumps(data, indent=2, default=str)
        mock_atomic_write.assert_called_once_with(path, expected_content)

    @patch("ovmobilebench.report.sink.atomic_write")
    @patch("ovmobilebench.report.sink.ensure_dir")
    def test_write_json_with_non_serializable_objects(self, mock_ensure_dir, mock_atomic_write):
        """Test writing JSON data with non-serializable objects (uses default=str)."""
        sink = JSONSink()

        # Create a non-serializable object
        class CustomObject:
            def __str__(self):
                return "custom_object"

        data = [{"name": "test", "obj": CustomObject()}]
        path = Path("/test/custom.json")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        # The custom object should be converted to string
        expected_content = json.dumps(data, indent=2, default=str)
        mock_atomic_write.assert_called_once_with(path, expected_content)

    @patch("ovmobilebench.report.sink.atomic_write", side_effect=IOError("Write failed"))
    @patch("ovmobilebench.report.sink.ensure_dir")
    def test_write_json_io_error(self, mock_ensure_dir, mock_atomic_write):
        """Test handling IOError during JSON write."""
        sink = JSONSink()
        data = [{"name": "test"}]
        path = Path("/test/fail.json")

        with pytest.raises(IOError):
            sink.write(data, path)

    @patch("ovmobilebench.report.sink.atomic_write")
    @patch("ovmobilebench.report.sink.ensure_dir", side_effect=OSError("Dir creation failed"))
    def test_write_json_dir_creation_error(self, mock_ensure_dir, mock_atomic_write):
        """Test handling directory creation error."""
        sink = JSONSink()
        data = [{"name": "test"}]
        path = Path("/test/fail.json")

        with pytest.raises(OSError):
            sink.write(data, path)


class TestCSVSink:
    """Test CSVSink implementation."""

    @patch("ovmobilebench.report.sink.ensure_dir")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_csv_simple_data(self, mock_file, mock_ensure_dir):
        """Test writing simple CSV data."""
        sink = CSVSink()
        data = [
            {"name": "test1", "value": 123},
            {"name": "test2", "value": 456},
        ]
        path = Path("/test/output.csv")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        mock_file.assert_called_once_with(path, "w", newline="")

        # Check that CSV writer was used correctly
        handle = mock_file.return_value.__enter__.return_value
        assert handle.write.called

    @patch("ovmobilebench.report.sink.ensure_dir")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_csv_empty_data(self, mock_file, mock_ensure_dir):
        """Test writing empty CSV data."""
        sink = CSVSink()
        data = []
        path = Path("/test/empty.csv")

        sink.write(data, path)

        # Should return early without creating file
        mock_ensure_dir.assert_not_called()
        mock_file.assert_not_called()

    @patch("ovmobilebench.report.sink.ensure_dir")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_csv_nested_data(self, mock_file, mock_ensure_dir):
        """Test writing CSV data with nested dictionaries."""
        sink = CSVSink()
        data = [
            {
                "experiment": "test",
                "results": {"throughput": 123.45, "latency": 1.0},
                "metadata": {"tag": "value"},
            }
        ]
        path = Path("/test/nested.csv")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        mock_file.assert_called_once_with(path, "w", newline="")

    def test_flatten_dict_simple(self):
        """Test flattening simple dictionary."""
        sink = CSVSink()
        data = {"name": "test", "value": 123}

        result = sink._flatten_dict(data)

        assert result == {"name": "test", "value": 123}

    def test_flatten_dict_nested(self):
        """Test flattening nested dictionary."""
        sink = CSVSink()
        data = {
            "name": "test",
            "results": {"throughput": 123.45, "latency": 1.0},
            "metadata": {"tag": "value", "nested": {"deep": "val"}},
        }

        result = sink._flatten_dict(data)

        expected = {
            "name": "test",
            "results_throughput": 123.45,
            "results_latency": 1.0,
            "metadata_tag": "value",
            "metadata_nested_deep": "val",
        }
        assert result == expected

    def test_flatten_dict_with_parent_key(self):
        """Test flattening dictionary with parent key."""
        sink = CSVSink()
        data = {"inner": {"value": 123}}

        result = sink._flatten_dict(data, "parent")

        assert result == {"parent_inner_value": 123}

    def test_flatten_dict_empty(self):
        """Test flattening empty dictionary."""
        sink = CSVSink()
        data = {}

        result = sink._flatten_dict(data)

        assert result == {}

    def test_flatten_dict_deeply_nested(self):
        """Test flattening deeply nested dictionary."""
        sink = CSVSink()
        data = {"level1": {"level2": {"level3": {"level4": "deep_value"}}}}

        result = sink._flatten_dict(data)

        assert result == {"level1_level2_level3_level4": "deep_value"}

    @patch("ovmobilebench.report.sink.ensure_dir")
    @patch("builtins.open", side_effect=IOError("File write failed"))
    def test_write_csv_io_error(self, mock_file, mock_ensure_dir):
        """Test handling IOError during CSV write."""
        sink = CSVSink()
        data = [{"name": "test"}]
        path = Path("/test/fail.csv")

        with pytest.raises(IOError):
            sink.write(data, path)

    @patch("ovmobilebench.report.sink.ensure_dir", side_effect=OSError("Dir creation failed"))
    def test_write_csv_dir_creation_error(self, mock_ensure_dir):
        """Test handling directory creation error."""
        sink = CSVSink()
        data = [{"name": "test"}]
        path = Path("/test/fail.csv")

        with pytest.raises(OSError):
            sink.write(data, path)

    @patch("ovmobilebench.report.sink.ensure_dir")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_csv_mixed_field_names(self, mock_file, mock_ensure_dir):
        """Test writing CSV with rows having different field names."""
        sink = CSVSink()
        data = [
            {"name": "test1", "value": 123},
            {"name": "test2", "score": 456},  # Different field name
            {"other": "test3", "value": 789},  # Another different field
        ]
        path = Path("/test/mixed.csv")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        mock_file.assert_called_once_with(path, "w", newline="")

    @patch("ovmobilebench.report.sink.ensure_dir")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_csv_with_none_values(self, mock_file, mock_ensure_dir):
        """Test writing CSV with None values."""
        sink = CSVSink()
        data = [
            {"name": "test1", "value": None},
            {"name": None, "value": 456},
        ]
        path = Path("/test/none_values.csv")

        sink.write(data, path)

        mock_ensure_dir.assert_called_once_with(path.parent)
        mock_file.assert_called_once_with(path, "w", newline="")
