"""Tests for benchmark runner module."""

from unittest.mock import MagicMock, call, patch

import pytest

from ovmobilebench.config.schema import RunConfig, RunMatrix
from ovmobilebench.devices.base import Device
from ovmobilebench.runners.benchmark import BenchmarkRunner


class TestBenchmarkRunner:
    """Test BenchmarkRunner class."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock device."""
        device = MagicMock(spec=Device)
        device.shell.return_value = (0, "benchmark output", "")
        return device

    @pytest.fixture
    def run_config(self):
        """Create a test run configuration."""
        return RunConfig(
            repeats=2,
            matrix=RunMatrix(
                niter=[100],
                api=["sync"],
                hint=["latency"],
                device=["CPU"],
                infer_precision=["FP16"],
            ),
            cooldown_sec=1,
            timeout_sec=60,
            warmup=False,
        )

    @pytest.fixture
    def benchmark_spec(self):
        """Create a test benchmark specification."""
        return {
            "model_name": "resnet50",
            "device": "CPU",
            "api": "sync",
            "niter": 100,
            "hint": "latency",
            "infer_precision": "FP16",
        }

    def test_init(self, mock_device, run_config):
        """Test BenchmarkRunner initialization."""
        runner = BenchmarkRunner(mock_device, run_config)

        assert runner.device == mock_device
        assert runner.config == run_config
        assert runner.remote_dir == "/data/local/tmp/ovmobilebench"

    def test_init_custom_remote_dir(self, mock_device, run_config):
        """Test BenchmarkRunner initialization with custom remote directory."""
        custom_dir = "/custom/path"
        runner = BenchmarkRunner(mock_device, run_config, remote_dir=custom_dir)

        assert runner.remote_dir == custom_dir

    @patch("ovmobilebench.runners.benchmark.time")
    def test_run_single_success(self, mock_time_module, mock_device, run_config, benchmark_spec):
        """Test successful single benchmark run."""
        mock_time_module.time.side_effect = [1000.0, 1005.0, 1005.5]  # start, end, timestamp
        mock_device.shell.return_value = (0, "benchmark output", "")

        runner = BenchmarkRunner(mock_device, run_config)
        result = runner.run_single(benchmark_spec)

        assert result["spec"] == benchmark_spec
        assert result["returncode"] == 0
        assert result["stdout"] == "benchmark output"
        assert result["stderr"] == ""
        assert result["duration_sec"] == 5.0
        assert result["timestamp"] == 1005.5
        assert "command" in result

    @patch("ovmobilebench.runners.benchmark.time")
    def test_run_single_failure(self, mock_time_module, mock_device, run_config, benchmark_spec):
        """Test failed single benchmark run."""
        mock_time_module.time.side_effect = [1000.0, 1005.0, 1005.5]
        mock_device.shell.return_value = (1, "", "error message")

        runner = BenchmarkRunner(mock_device, run_config)
        result = runner.run_single(benchmark_spec)

        assert result["returncode"] == 1
        assert result["stderr"] == "error message"

    def test_run_single_with_timeout(self, mock_device, run_config, benchmark_spec):
        """Test single benchmark run with custom timeout."""
        runner = BenchmarkRunner(mock_device, run_config)
        runner.run_single(benchmark_spec, timeout=120)

        mock_device.shell.assert_called_once()
        args, kwargs = mock_device.shell.call_args
        assert kwargs["timeout"] == 120

    def test_run_single_with_config_timeout(self, mock_device, run_config, benchmark_spec):
        """Test single benchmark run using config timeout."""
        runner = BenchmarkRunner(mock_device, run_config)
        runner.run_single(benchmark_spec)

        mock_device.shell.assert_called_once()
        args, kwargs = mock_device.shell.call_args
        assert kwargs["timeout"] == 60  # config timeout_sec

    def test_run_single_no_timeout(self, mock_device, benchmark_spec):
        """Test single benchmark run with no timeout configured."""
        config = RunConfig(
            repeats=1,
            matrix=RunMatrix(),
            timeout_sec=None,
        )
        runner = BenchmarkRunner(mock_device, config)
        runner.run_single(benchmark_spec)

        mock_device.shell.assert_called_once()
        args, kwargs = mock_device.shell.call_args
        assert kwargs["timeout"] is None

    @patch("time.sleep")
    def test_run_matrix(self, mock_sleep, mock_device, run_config):
        """Test running matrix of benchmarks."""
        matrix_specs = [
            {
                "model_name": "model1",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "latency",
            },
            {
                "model_name": "model2",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "throughput",
            },
        ]

        runner = BenchmarkRunner(mock_device, run_config)
        results = runner.run_matrix(matrix_specs)

        # 2 specs * 2 repeats = 4 results
        assert len(results) == 4

        # Check repeat numbers
        assert results[0]["repeat"] == 0
        assert results[1]["repeat"] == 1
        assert results[2]["repeat"] == 0
        assert results[3]["repeat"] == 1

        # Check cooldown was called (3 times between 4 runs)
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(1), call(1), call(1)])

    def test_run_matrix_no_cooldown(self, mock_device):
        """Test running matrix without cooldown."""
        config = RunConfig(
            repeats=1,
            matrix=RunMatrix(),
            cooldown_sec=0,
        )
        matrix_specs = [
            {
                "model_name": "model1",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "latency",
            }
        ]

        runner = BenchmarkRunner(mock_device, config)

        with patch("time.sleep") as mock_sleep:
            runner.run_matrix(matrix_specs)
            mock_sleep.assert_not_called()

    def test_run_matrix_with_progress_callback(self, mock_device, run_config):
        """Test running matrix with progress callback."""
        matrix_specs = [
            {
                "model_name": "model1",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "latency",
            }
        ]
        progress_callback = MagicMock()

        runner = BenchmarkRunner(mock_device, run_config)
        runner.run_matrix(matrix_specs, progress_callback)

        # Should be called for each completed run
        # Filter out __bool__ calls
        actual_calls = [
            c for c in progress_callback.call_args_list if not str(c).endswith("__bool__()")
        ]
        assert len(actual_calls) == 2  # 1 spec * 2 repeats
        assert actual_calls == [call(1, 2), call(2, 2)]

    def test_build_command_basic(self, mock_device, run_config, benchmark_spec):
        """Test building basic benchmark command."""
        runner = BenchmarkRunner(mock_device, run_config)
        cmd = runner._build_command(benchmark_spec)

        expected_parts = [
            "cd /data/local/tmp/ovmobilebench",
            "export LD_LIBRARY_PATH=/data/local/tmp/ovmobilebench/lib:$LD_LIBRARY_PATH",
            "./bin/benchmark_app",
            "-m models/resnet50.xml",
            "-d CPU",
            "-api sync",
            "-niter 100",
            "-hint latency",
            "-infer_precision FP16",
        ]

        for part in expected_parts:
            assert part in cmd

    def test_build_command_gpu_device(self, mock_device, run_config):
        """Test building command for GPU device."""
        spec = {
            "model_name": "resnet50",
            "device": "GPU",
            "api": "sync",
            "niter": 100,
            "hint": "throughput",
            "infer_precision": "FP16",
        }

        runner = BenchmarkRunner(mock_device, run_config)
        cmd = runner._build_command(spec)

        assert "-d GPU" in cmd
        assert "-hint throughput" in cmd

    def test_build_command_missing_optional_fields(self, mock_device, run_config):
        """Test building command with missing optional fields."""
        spec = {
            "model_name": "resnet50",
            "device": "CPU",
            "api": "sync",
            "niter": 100,
            # Missing hint and infer_precision
        }

        runner = BenchmarkRunner(mock_device, run_config)
        cmd = runner._build_command(spec)

        assert "-m models/resnet50.xml" in cmd
        assert "-d CPU" in cmd
        assert "-hint" not in cmd
        assert "-infer_precision" not in cmd

    def test_build_command_hint_none_with_fine_tuning(self, mock_device, run_config):
        """Test building command with hint=none allows fine-tuning options."""
        spec = {
            "model_name": "resnet50",
            "device": "CPU",
            "api": "sync",
            "niter": 100,
            "hint": "none",
            "nireq": 2,
            "nstreams": "4",
            "threads": 8,
            "infer_precision": "FP16",
        }

        runner = BenchmarkRunner(mock_device, run_config)
        cmd = runner._build_command(spec)

        assert "-hint none" in cmd
        assert "-nireq 2" in cmd
        assert "-nstreams 4" in cmd
        assert "-nthreads 8" in cmd
        assert "-infer_precision FP16" in cmd

    def test_build_command_custom_remote_dir(self, mock_device, run_config, benchmark_spec):
        """Test building command with custom remote directory."""
        runner = BenchmarkRunner(mock_device, run_config, remote_dir="/custom/path")
        cmd = runner._build_command(benchmark_spec)

        assert "cd /custom/path" in cmd
        assert "export LD_LIBRARY_PATH=/custom/path/lib:$LD_LIBRARY_PATH" in cmd

    def test_warmup(self, mock_device, run_config):
        """Test warmup functionality."""
        runner = BenchmarkRunner(mock_device, run_config)
        runner.warmup("test_model")

        # Verify device.shell was called with warmup parameters
        mock_device.shell.assert_called_once()
        args, kwargs = mock_device.shell.call_args

        # Check timeout
        assert kwargs["timeout"] == 30

        # Check command contains warmup-specific parameters
        cmd = args[0]
        assert "-m models/test_model.xml" in cmd
        assert "-d CPU" in cmd
        assert "-api sync" in cmd
        assert "-niter 10" in cmd
        assert "-hint latency" in cmd

    def test_run_single_logs_command(self, mock_device, run_config, benchmark_spec):
        """Test that run_single logs the command being executed."""
        runner = BenchmarkRunner(mock_device, run_config)

        with patch("ovmobilebench.runners.benchmark.logger") as mock_logger:
            runner.run_single(benchmark_spec)

            # Check that info was called with the command
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert log_call.startswith("Running:")

    def test_run_single_logs_error_on_failure(self, mock_device, run_config, benchmark_spec):
        """Test that run_single logs error on benchmark failure."""
        mock_device.shell.return_value = (1, "", "benchmark failed")
        runner = BenchmarkRunner(mock_device, run_config)

        with patch("ovmobilebench.runners.benchmark.logger") as mock_logger:
            runner.run_single(benchmark_spec)

            # Check that error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "Benchmark failed with rc=1: benchmark failed" in error_call

    def test_run_matrix_logs_progress(self, mock_device, run_config):
        """Test that run_matrix logs progress information."""
        matrix_specs = [
            {
                "model_name": "model1",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "latency",
            }
        ]
        runner = BenchmarkRunner(mock_device, run_config)

        with patch("ovmobilebench.runners.benchmark.logger") as mock_logger:
            runner.run_matrix(matrix_specs)

            # Should log progress for each repeat
            assert mock_logger.info.call_count >= 2  # At least one for each repeat

            # Check specific log messages
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("repeat 1/2" in call for call in log_calls)
            assert any("repeat 2/2" in call for call in log_calls)

    def test_run_matrix_logs_cooldown(self, mock_device, run_config):
        """Test that run_matrix logs cooldown information."""
        matrix_specs = [
            {
                "model_name": "model1",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "latency",
            },
            {
                "model_name": "model2",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "hint": "throughput",
            },
        ]
        runner = BenchmarkRunner(mock_device, run_config)

        with patch("ovmobilebench.runners.benchmark.logger") as mock_logger:
            with patch("time.sleep"):
                runner.run_matrix(matrix_specs)

                # Should log cooldown messages
                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                cooldown_logs = [call for call in log_calls if "Cooldown for" in call]
                assert len(cooldown_logs) == 3  # Between 4 total runs

    def test_warmup_logs_message(self, mock_device, run_config):
        """Test that warmup logs appropriate message."""
        runner = BenchmarkRunner(mock_device, run_config)

        with patch("ovmobilebench.runners.benchmark.logger") as mock_logger:
            runner.warmup("test_model")

            # Check that the warmup message was logged (it's the first call)
            assert any(
                "Warmup run for test_model" in str(call) for call in mock_logger.info.call_args_list
            )
