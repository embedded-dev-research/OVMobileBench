#!/usr/bin/env python3
"""
Validate benchmark results.
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_report_files():
    """Find all report.json files in artifacts."""
    project_root = Path(__file__).parent.parent.parent
    artifacts_dir = project_root / "artifacts"

    if not artifacts_dir.exists():
        logger.error("No artifacts directory found")
        return []

    reports = list(artifacts_dir.rglob("report.json"))
    return reports


def validate_report(report_path: Path):
    """Validate a single report file."""
    logger.info(f"Validating {report_path}")

    with open(report_path) as f:
        data = json.load(f)

    # Check structure
    if "results" not in data:
        logger.error("No 'results' field in report")
        return False

    if not data["results"]:
        logger.error("Results array is empty")
        return False

    # Validate each result
    for idx, result in enumerate(data["results"]):
        required_fields = ["model_name", "throughput", "latency_avg"]

        for field in required_fields:
            if field not in result:
                logger.error(f"Result {idx} missing field: {field}")
                return False

        # Validate throughput
        throughput = result.get("throughput", 0)
        if throughput <= 0:
            logger.error(f"Invalid throughput: {throughput}")
            return False

        if throughput > 10000:
            logger.warning(f"Unusually high throughput: {throughput}")

        # Validate latency
        latency = result.get("latency_avg", 0)
        if latency <= 0:
            logger.error(f"Invalid latency: {latency}")
            return False

    logger.info(f"Report validation passed: {len(data['results'])} results")
    return True


def main():
    """Main validation entry point."""
    reports = find_report_files()

    if not reports:
        logger.error("No report files found to validate")
        sys.exit(1)

    logger.info(f"Found {len(reports)} report(s) to validate")

    all_valid = True
    for report in reports:
        if not validate_report(report):
            all_valid = False

    if all_valid:
        logger.info("All reports validated successfully!")
        sys.exit(0)
    else:
        logger.error("Some reports failed validation")
        sys.exit(1)


if __name__ == "__main__":
    main()
