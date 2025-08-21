#!/usr/bin/env python3
"""
Display benchmark results in a nice format.
"""

import json
import logging
from pathlib import Path

from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_latest_report():
    """Find the most recent report.json file."""
    project_root = Path(__file__).parent.parent.parent
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        return None

    reports = list(artifacts_dir.rglob("report.json"))
    if not reports:
        return None

    # Get the most recent one
    return max(reports, key=lambda p: p.stat().st_mtime)


def display_report(report_path: Path):
    """Display report in a nice table format."""
    with open(report_path) as f:
        data = json.load(f)

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)

    if "metadata" in data:
        print("\nMetadata:")
        for key, value in data["metadata"].items():
            print(f"  {key}: {value}")

    if "results" in data and data["results"]:
        print("\nPerformance Metrics:")

        # Prepare table data
        headers = ["Model", "Device", "Throughput (FPS)", "Latency (ms)", "Threads"]
        rows = []

        for result in data["results"]:
            rows.append(
                [
                    result.get("model_name", "N/A"),
                    result.get("device", "N/A"),
                    f"{result.get('throughput', 0):.2f}",
                    f"{result.get('latency_avg', 0):.2f}",
                    result.get("threads", "N/A"),
                ]
            )

        print(tabulate(rows, headers=headers, tablefmt="grid"))

        # Summary statistics
        print("\nSummary:")
        throughputs = [r.get("throughput", 0) for r in data["results"]]
        latencies = [r.get("latency_avg", 0) for r in data["results"]]

        if throughputs:
            print(f"  Average Throughput: {sum(throughputs)/len(throughputs):.2f} FPS")
            print(f"  Best Throughput: {max(throughputs):.2f} FPS")

        if latencies:
            print(f"  Average Latency: {sum(latencies)/len(latencies):.2f} ms")
            print(f"  Best Latency: {min(latencies):.2f} ms")

    print("=" * 80 + "\n")


def main():
    """Main entry point."""
    report = find_latest_report()

    if not report:
        logger.error("No report files found")
        return

    logger.info(f"Displaying results from: {report}")
    display_report(report)


if __name__ == "__main__":
    main()
