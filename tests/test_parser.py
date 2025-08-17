"""Tests for benchmark output parser."""

import pytest

from ovmobilebench.parsers.benchmark_parser import BenchmarkParser, parse_metrics


class TestParseMetrics:
    """Test parse_metrics function."""

    def test_parse_throughput(self):
        """Test parsing throughput from output."""
        output = """
        [Step 10/11] Measuring performance (Start inference asynchronously, 200 inference requests, limits: 60000 ms duration)
        [Step 11/11] Dumping statistics report
        Count:          200 iterations
        Duration:       1234.56 ms
        Throughput:     162.07 FPS
        """
        metrics = parse_metrics(output)
        assert metrics["throughput_fps"] == pytest.approx(162.07)

    def test_parse_latencies(self):
        """Test parsing latency metrics."""
        output = """
        Average latency: 12.34 ms
        Median latency: 11.50 ms
        Min latency: 10.20 ms
        Max latency: 15.80 ms
        """
        metrics = parse_metrics(output)
        assert metrics["latency_avg_ms"] == pytest.approx(12.34)
        assert metrics["latency_med_ms"] == pytest.approx(11.50)
        assert metrics["latency_min_ms"] == pytest.approx(10.20)
        assert metrics["latency_max_ms"] == pytest.approx(15.80)

    def test_parse_count(self):
        """Test parsing iteration count."""
        output = "count: 200"
        metrics = parse_metrics(output)
        assert metrics["iterations"] == 200

    def test_parse_device_info(self):
        """Test parsing device information."""
        output = "Device: CPU"
        metrics = parse_metrics(output)
        assert metrics["raw_device_line"] == "CPU"

    def test_empty_output(self):
        """Test parsing empty output."""
        metrics = parse_metrics("")
        assert metrics == {}

    def test_partial_output(self):
        """Test parsing partial output with only some metrics."""
        output = "Throughput: 100.5 FPS"
        metrics = parse_metrics(output)
        assert metrics["throughput_fps"] == pytest.approx(100.5)
        assert "latency_avg_ms" not in metrics


class TestBenchmarkParser:
    """Test BenchmarkParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return BenchmarkParser()

    def test_parse_successful_result(self, parser):
        """Test parsing successful benchmark result."""
        result = {
            "spec": {
                "model_name": "resnet50",
                "device": "CPU",
                "niter": 200,
            },
            "repeat": 0,
            "returncode": 0,
            "stdout": "Throughput: 100.0 FPS\nAverage latency: 10.0 ms",
            "stderr": "",
            "duration_sec": 5.0,
            "timestamp": 1234567890,
        }

        parsed = parser.parse_result(result)

        assert parsed["model_name"] == "resnet50"
        assert parsed["device"] == "CPU"
        assert parsed["niter"] == 200
        assert parsed["repeat"] == 0
        assert parsed["returncode"] == 0
        assert parsed["throughput_fps"] == pytest.approx(100.0)
        assert parsed["latency_avg_ms"] == pytest.approx(10.0)

    def test_parse_failed_result(self, parser):
        """Test parsing failed benchmark result."""
        result = {
            "spec": {"model_name": "resnet50"},
            "returncode": 1,
            "stdout": "",
            "stderr": "Error: Model not found",
            "duration_sec": 0.1,
            "timestamp": 1234567890,
        }

        parsed = parser.parse_result(result)

        assert parsed["returncode"] == 1
        assert parsed["error"] == "Error: Model not found"
        assert "throughput_fps" not in parsed

    def test_aggregate_results(self, parser):
        """Test aggregating multiple results."""
        results = [
            {
                "model_name": "resnet50",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "throughput_fps": 100.0,
                "latency_avg_ms": 10.0,
            },
            {
                "model_name": "resnet50",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "throughput_fps": 110.0,
                "latency_avg_ms": 9.0,
            },
            {
                "model_name": "resnet50",
                "device": "CPU",
                "api": "sync",
                "niter": 100,
                "throughput_fps": 105.0,
                "latency_avg_ms": 9.5,
            },
        ]

        aggregated = parser.aggregate_results(results)

        assert len(aggregated) == 1
        agg = aggregated[0]
        assert agg["repeats"] == 3
        assert agg["throughput_fps_mean"] == pytest.approx(105.0)
        assert agg["throughput_fps_median"] == pytest.approx(105.0)
        assert agg["throughput_fps_min"] == pytest.approx(100.0)
        assert agg["throughput_fps_max"] == pytest.approx(110.0)
        assert agg["latency_avg_ms_mean"] == pytest.approx(9.5)

    def test_aggregate_empty_results(self, parser):
        """Test aggregating empty results."""
        aggregated = parser.aggregate_results([])
        assert aggregated == []

    def test_config_key_generation(self, parser):
        """Test configuration key generation."""
        result = {
            "model_name": "resnet50",
            "device": "CPU",
            "api": "sync",
            "niter": 100,
            "nireq": 1,
            "nstreams": "1",
            "threads": 4,
            "infer_precision": "FP16",
        }

        key = parser._get_config_key(result)

        assert "model_name=resnet50" in key
        assert "device=CPU" in key
        assert "api=sync" in key
        assert "threads=4" in key
