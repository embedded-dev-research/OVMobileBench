"""Parser for benchmark_app output."""

import re
from typing import Any, Dict


def parse_metrics(output: str) -> Dict[str, Any]:
    """Parse benchmark_app output to extract metrics."""
    metrics: Dict[str, Any] = {}

    # Parse throughput
    throughput_match = re.search(r"Throughput:\s*([\d.]+)\s*FPS", output)
    if throughput_match:
        metrics["throughput_fps"] = float(throughput_match.group(1))

    # Parse latencies
    latency_patterns = [
        (r"Average latency:\s*([\d.]+)\s*ms", "latency_avg_ms"),
        (r"Median latency:\s*([\d.]+)\s*ms", "latency_med_ms"),
        (r"Min latency:\s*([\d.]+)\s*ms", "latency_min_ms"),
        (r"Max latency:\s*([\d.]+)\s*ms", "latency_max_ms"),
    ]

    for pattern, key in latency_patterns:
        match = re.search(pattern, output)
        if match:
            metrics[key] = float(match.group(1))

    # Parse count/iterations
    count_match = re.search(r"count:\s*(\d+)", output)
    if count_match:
        metrics["iterations"] = int(count_match.group(1))

    # Parse device info
    device_match = re.search(r"Device:\s*(.+)", output)
    if device_match:
        metrics["raw_device_line"] = device_match.group(1).strip()

    return metrics


class BenchmarkParser:
    """Parse and aggregate benchmark results."""

    def parse_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse single benchmark result."""
        parsed = {
            **result["spec"],
            "repeat": result.get("repeat", 0),
            "returncode": result["returncode"],
            "duration_sec": result["duration_sec"],
            "timestamp": result["timestamp"],
        }

        if result["returncode"] == 0:
            metrics = parse_metrics(result["stdout"])
            parsed.update(metrics)
        else:
            parsed["error"] = result["stderr"]

        return parsed

    def aggregate_results(self, results: list) -> list:
        """Aggregate multiple runs of the same configuration."""
        if not results:
            return []

        # Group by configuration
        grouped: Dict[str, list] = {}
        for result in results:
            key = self._get_config_key(result)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)

        aggregated = []
        for key, group in grouped.items():
            # Extract metrics
            fps_values = [r.get("throughput_fps") for r in group if r.get("throughput_fps")]
            lat_avg_values = [r.get("latency_avg_ms") for r in group if r.get("latency_avg_ms")]

            agg = {
                **group[0],  # Copy spec fields
                "repeats": len(group),
            }

            if fps_values:
                agg["throughput_fps_mean"] = sum(fps_values) / len(fps_values)
                agg["throughput_fps_median"] = sorted(fps_values)[len(fps_values) // 2]
                agg["throughput_fps_min"] = min(fps_values)
                agg["throughput_fps_max"] = max(fps_values)

            if lat_avg_values:
                agg["latency_avg_ms_mean"] = sum(lat_avg_values) / len(lat_avg_values)
                agg["latency_avg_ms_median"] = sorted(lat_avg_values)[len(lat_avg_values) // 2]

            aggregated.append(agg)

        return aggregated

    def _get_config_key(self, result: Dict[str, Any]) -> str:
        """Generate unique key for configuration."""
        key_fields = [
            "model_name",
            "device",
            "api",
            "niter",
            "nireq",
            "nstreams",
            "threads",
            "infer_precision",
        ]

        key_parts = []
        for field in key_fields:
            if field in result:
                key_parts.append(f"{field}={result[field]}")

        return "|".join(key_parts)
