"""Mock display results module for testing."""

import json
from pathlib import Path


def find_latest_report():
    """Find the latest report file."""
    project_root = Path(__file__).parent.parent.parent
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        return None

    # Look for report.json or report_*.json files
    report_files = list(artifacts_dir.glob("**/report.json"))
    report_files.extend(artifacts_dir.glob("**/report_*.json"))

    if not report_files:
        return None

    # Return the most recent report
    return max(report_files, key=lambda p: p.stat().st_mtime)


def display_report(report_path=None):
    """Display report data."""
    if report_path is None:
        report_path = find_latest_report()

    if report_path is None or not Path(report_path).exists():
        print("No report found")
        return

    try:
        with open(report_path) as f:
            data = json.load(f)

        # Print metadata
        if "metadata" in data:
            print("\n=== Metadata ===")
            for key, value in data["metadata"].items():
                print(f"{key}: {value}")

        # Print results in table format
        if "results" in data and data["results"]:
            print("\n=== Performance Results ===")

            # Try to use tabulate if available
            try:
                import tabulate

                headers = ["Model", "Device", "Throughput", "Latency", "Threads"]
                rows = []
                for result in data["results"]:
                    rows.append(
                        [
                            result.get("model_name", "N/A"),
                            result.get("device", "N/A"),
                            (
                                f"{result.get('throughput', 0):.2f}"
                                if "throughput" in result
                                else "N/A"
                            ),
                            (
                                f"{result.get('latency_avg', 0):.2f}"
                                if "latency_avg" in result
                                else "N/A"
                            ),
                            result.get("threads", "N/A"),
                        ]
                    )
                print(tabulate.tabulate(rows, headers=headers, tablefmt="grid"))
            except ImportError:
                # Fallback to simple printing
                for result in data["results"]:
                    print(f"Model: {result.get('model_name', 'N/A')}")
                    print(f"  Device: {result.get('device', 'N/A')}")
                    print(f"  Throughput: {result.get('throughput', 'N/A')}")
                    print(f"  Latency: {result.get('latency_avg', 'N/A')}")
                    print()
    except Exception as e:
        print(f"Error reading report: {e}")


def main():
    """Main entry point."""
    display_report()


if __name__ == "__main__":
    main()
