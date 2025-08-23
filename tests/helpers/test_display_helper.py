"""Tests for display results functionality."""

import json

# Import from e2e helper scripts
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent / "tests" / "e2e"))

# Import the display functions
from test_display_results import (
    display_report,
    find_latest_report,
    main,
)


class TestDisplayHelper:
    """Test result display functions."""

    def test_find_latest_report_no_artifacts_dir(self):
        """Test finding latest report when artifacts directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            with patch("test_display_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                report = find_latest_report()

                assert report is None

    def test_find_latest_report_empty_artifacts_dir(self):
        """Test finding latest report in empty artifacts directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"
            artifacts_dir.mkdir()

            with patch("test_display_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                report = find_latest_report()

                assert report is None

    def test_find_latest_report_single_report(self):
        """Test finding latest report with single report file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"
            run_dir = artifacts_dir / "run1"
            run_dir.mkdir(parents=True)

            report_path = run_dir / "report.json"
            report_path.touch()

            with patch("test_display_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                report = find_latest_report()

                assert report == report_path

    def test_find_latest_report_multiple_reports(self):
        """Test finding latest report among multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"

            # Create multiple run directories
            run1_dir = artifacts_dir / "run1"
            run2_dir = artifacts_dir / "run2"
            run1_dir.mkdir(parents=True)
            run2_dir.mkdir(parents=True)

            # Create reports with different timestamps
            report1_path = run1_dir / "report.json"
            report2_path = run2_dir / "report.json"
            report1_path.touch()

            # Ensure second report is newer
            import time

            time.sleep(0.01)
            report2_path.touch()

            with patch("test_display_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                report = find_latest_report()

                assert report == report2_path

    def test_display_report_with_metadata(self):
        """Test displaying report with metadata section."""
        report_data = {
            "metadata": {
                "run_id": "test_run_123",
                "timestamp": "2024-01-01T12:00:00Z",
                "device": "TestDevice",
            },
            "results": [
                {
                    "model_name": "resnet50",
                    "device": "CPU",
                    "throughput": 25.5,
                    "latency_avg": 39.2,
                    "threads": 4,
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)

                # Check that metadata was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                metadata_calls = [
                    call for call in print_calls if "Metadata" in call or "run_id" in call
                ]
                assert len(metadata_calls) > 0

                # Check specific metadata fields
                run_id_calls = [call for call in print_calls if "run_id" in call]
                assert len(run_id_calls) > 0
        finally:
            report_path.unlink()

    def test_display_report_performance_table(self):
        """Test displaying performance metrics table."""
        report_data = {
            "results": [
                {
                    "model_name": "resnet50",
                    "device": "CPU",
                    "throughput": 25.5,
                    "latency_avg": 39.2,
                    "threads": 4,
                },
                {
                    "model_name": "mobilenet",
                    "device": "GPU",
                    "throughput": 45.8,
                    "latency_avg": 21.8,
                    "threads": 2,
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)
                # Just verify function was called and output was produced
                mock_print.assert_called()
        finally:
            report_path.unlink()

    def test_display_report_summary_statistics(self):
        """Test displaying summary statistics."""
        report_data = {
            "results": [
                {
                    "model_name": "model1",
                    "throughput": 20.0,
                    "latency_avg": 50.0,
                },
                {
                    "model_name": "model2",
                    "throughput": 30.0,
                    "latency_avg": 33.3,
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)

                # Check that results were printed
                print_calls = [str(call) for call in mock_print.call_args_list]

                # Should print model names
                model_calls = [call for call in print_calls if "model1" in call or "model2" in call]
                assert len(model_calls) > 0

        finally:
            report_path.unlink()

    def test_display_report_empty_results(self):
        """Test displaying report with empty results."""
        report_data = {"metadata": {"run_id": "test"}, "results": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)

                # Should be called at least once
                mock_print.assert_called()
        finally:
            report_path.unlink()

    def test_display_report_no_results_field(self):
        """Test displaying report without results field."""
        report_data = {"metadata": {"run_id": "test"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)

                # Should display metadata
                print_calls = [str(call) for call in mock_print.call_args_list]
                metadata_calls = [
                    call for call in print_calls if "Metadata" in call or "run_id" in call
                ]
                assert len(metadata_calls) > 0
        finally:
            report_path.unlink()

    def test_display_report_missing_optional_fields(self):
        """Test displaying report with missing optional fields."""
        report_data = {
            "results": [
                {
                    "model_name": "resnet50",
                    "throughput": 25.5,
                    "latency_avg": 39.2,
                    # Missing device, threads
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)

                # Check that the report was displayed (tabulate will be used internally)
                mock_print.assert_called()
                # Check that N/A was printed for missing fields
                print_output = str(mock_print.call_args_list)
                assert "N/A" in print_output or "resnet50" in print_output
        finally:
            report_path.unlink()

    def test_display_report_malformed_json(self):
        """Test displaying report with malformed JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                display_report(report_path)
                # Should print error message about malformed JSON
                error_calls = [call for call in mock_print.call_args_list if "Error" in str(call)]
                assert len(error_calls) > 0
        finally:
            report_path.unlink()


class TestDisplayMain:
    """Test display main function."""

    def test_main_no_report_found(self):
        """Test main function when no report is found."""
        with patch("test_display_results.find_latest_report", return_value=None):
            main()  # Should not raise exception

    def test_main_report_found(self):
        """Test main function when report is found."""
        mock_report_path = Path("test_report.json")

        with patch("test_display_results.find_latest_report", return_value=mock_report_path):
            with patch("test_display_results.display_report") as mock_display:
                main()

                mock_display.assert_called_once_with()

    def test_main_display_exception(self):
        """Test main function when display_report raises exception."""
        mock_report_path = Path("test_report.json")

        with patch("test_display_results.find_latest_report", return_value=mock_report_path):
            with patch(
                "test_display_results.display_report", side_effect=Exception("Display error")
            ):
                with pytest.raises(Exception, match="Display error"):
                    main()


class TestDisplayIntegration:
    """Integration tests for display functionality."""

    def test_complete_display_workflow(self):
        """Test complete workflow from finding to displaying report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            artifacts_dir = project_root / "artifacts"
            run_dir = artifacts_dir / "test_run"
            run_dir.mkdir(parents=True)

            # Create comprehensive report
            report_data = {
                "metadata": {
                    "run_id": "integration_test",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "device": "TestDevice",
                },
                "results": [
                    {
                        "model_name": "resnet50",
                        "device": "CPU",
                        "throughput": 25.5,
                        "latency_avg": 39.2,
                        "threads": 4,
                    },
                    {
                        "model_name": "mobilenet",
                        "device": "CPU",
                        "throughput": 45.8,
                        "latency_avg": 21.8,
                        "threads": 4,
                    },
                ],
            }

            report_path = run_dir / "report.json"
            with open(report_path, "w") as f:
                json.dump(report_data, f)

            with patch("test_display_results.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = project_root
                mock_path.__file__ = __file__

                # Find latest report
                latest_report = find_latest_report()
                assert latest_report == report_path

                # Display report (should not raise exception)
                with patch("builtins.print") as mock_print:
                    display_report(latest_report)
                    # Verify display_report was called successfully
                    mock_print.assert_called()

    def test_display_edge_case_values(self):
        """Test displaying report with edge case numeric values."""
        report_data = {
            "results": [
                {
                    "model_name": "edge_case_model",
                    "device": "CPU",
                    "throughput": 0.001,  # Very small
                    "latency_avg": 9999.999,  # Very large
                    "threads": 1,
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(report_data, f)
            report_path = Path(f.name)

        try:
            with patch("builtins.print") as mock_print:
                # Should not raise exception
                display_report(report_path)

                # Verify edge case values are handled
                mock_print.assert_called()
                print_output = str(mock_print.call_args_list)
                # Check that the edge case values were processed without errors
                assert "edge_case_model" in print_output or "CPU" in print_output
        finally:
            report_path.unlink()
