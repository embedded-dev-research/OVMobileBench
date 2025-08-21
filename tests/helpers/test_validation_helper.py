"""Tests for result validation functionality."""

import json

# Import from e2e helper scripts
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent / "tests" / "e2e"))

from test_validate_results import (
    find_report_files,
    main,
    validate_report,
)


class TestValidationHelper:
    """Test result validation functions."""

    def test_find_report_files_no_artifacts_dir(self):
        """Test finding reports when artifacts directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_validate_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                reports = find_report_files()

                assert reports == []

    def test_find_report_files_empty_artifacts_dir(self):
        """Test finding reports in empty artifacts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"
            artifacts_dir.mkdir()

            with patch("test_validate_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                reports = find_report_files()

                assert reports == []

    def test_find_report_files_with_reports(self):
        """Test finding multiple report files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"

            # Create nested structure with multiple reports
            run1_dir = artifacts_dir / "run1"
            run2_dir = artifacts_dir / "run2" / "reports"
            run1_dir.mkdir(parents=True)
            run2_dir.mkdir(parents=True)

            report1 = run1_dir / "report.json"
            report2 = run2_dir / "report.json"
            report1.touch()
            report2.touch()

            # Create non-report files (should be ignored)
            (run1_dir / "other.json").touch()
            (run2_dir / "summary.txt").touch()

            with patch("test_validate_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                reports = find_report_files()

                assert len(reports) == 2
                report_names = {r.name for r in reports}
                assert report_names == {"report.json"}

    def test_validate_report_valid_structure(self):
        """Test validating a properly structured report."""
        valid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 25.5,
                    "latency_avg": 39.2,
                    "device": "CPU",
                },
                {
                    "model_name": "mobilenet",
                    "throughput": 45.8,
                    "latency_avg": 21.8,
                    "device": "CPU",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is True
        finally:
            report_path.unlink()

    def test_validate_report_missing_results_field(self):
        """Test validation failure when results field is missing."""
        invalid_report = {"metadata": {"run_id": "test"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_empty_results(self):
        """Test validation failure when results array is empty."""
        invalid_report = {"results": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_missing_required_fields(self):
        """Test validation failure when required fields are missing."""
        invalid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    # Missing throughput and latency_avg
                    "device": "CPU",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_invalid_throughput_zero(self):
        """Test validation failure for zero throughput."""
        invalid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 0.0,
                    "latency_avg": 39.2,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_invalid_throughput_negative(self):
        """Test validation failure for negative throughput."""
        invalid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": -5.0,
                    "latency_avg": 39.2,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_very_high_throughput_warning(self):
        """Test warning for unusually high throughput."""
        report_with_high_throughput = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 15000.0,  # Very high
                    "latency_avg": 0.1,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_with_high_throughput, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            # Should still pass validation but warn
            assert result is True
        finally:
            report_path.unlink()

    def test_validate_report_invalid_latency_zero(self):
        """Test validation failure for zero latency."""
        invalid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 25.5,
                    "latency_avg": 0.0,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_invalid_latency_negative(self):
        """Test validation failure for negative latency."""
        invalid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 25.5,
                    "latency_avg": -10.0,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is False
        finally:
            report_path.unlink()

    def test_validate_report_multiple_results(self):
        """Test validation with multiple results."""
        valid_report = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 25.5,
                    "latency_avg": 39.2,
                },
                {
                    "model_name": "mobilenet",
                    "throughput": 45.8,
                    "latency_avg": 21.8,
                },
                {
                    "model_name": "efficientnet",
                    "throughput": 35.2,
                    "latency_avg": 28.4,
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is True
        finally:
            report_path.unlink()

    def test_validate_report_malformed_json(self):
        """Test validation with malformed JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')  # Malformed JSON
            report_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                validate_report(report_path)
        finally:
            report_path.unlink()


class TestValidationMain:
    """Test validation main function."""

    def test_main_no_reports_found(self):
        """Test main function when no reports are found."""
        with patch("test_validate_results.find_report_files", return_value=[]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_all_reports_valid(self):
        """Test main function when all reports are valid."""
        mock_reports = [Path("report1.json"), Path("report2.json")]

        with patch("test_validate_results.find_report_files", return_value=mock_reports):
            with patch("test_validate_results.validate_report", return_value=True):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 0

    def test_main_some_reports_invalid(self):
        """Test main function when some reports are invalid."""
        mock_reports = [Path("report1.json"), Path("report2.json")]

        with patch("test_validate_results.find_report_files", return_value=mock_reports):
            with patch("test_validate_results.validate_report", side_effect=[True, False]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                assert exc_info.value.code == 1

    def test_main_validation_exception(self):
        """Test main function when validation raises exception."""
        mock_reports = [Path("report1.json")]

        with patch("test_validate_results.find_report_files", return_value=mock_reports):
            with patch(
                "test_validate_results.validate_report", side_effect=Exception("Validation error")
            ):
                with pytest.raises(Exception, match="Validation error"):
                    main()


class TestValidationIntegration:
    """Integration tests for validation functionality."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow from finding to validating reports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"
            run_dir = artifacts_dir / "test_run"
            run_dir.mkdir(parents=True)

            # Create valid report
            valid_report = {
                "results": [
                    {
                        "model_name": "resnet50",
                        "throughput": 25.5,
                        "latency_avg": 39.2,
                    }
                ]
            }

            report_path = run_dir / "report.json"
            with open(report_path, "w") as f:
                json.dump(valid_report, f)

            with patch("test_validate_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                # Find reports
                reports = find_report_files()
                assert len(reports) == 1

                # Validate report
                is_valid = validate_report(reports[0])
                assert is_valid is True

    def test_validation_with_edge_case_values(self):
        """Test validation with edge case numeric values."""
        edge_case_report = {
            "results": [
                {
                    "model_name": "test_model",
                    "throughput": 0.001,  # Very small but valid
                    "latency_avg": 9999.9,  # Very large but valid
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(edge_case_report, f)
            report_path = Path(f.name)

        try:
            result = validate_report(report_path)
            assert result is True
        finally:
            report_path.unlink()
