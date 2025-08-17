"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    """Automatically skip tests listed in skip_list.txt."""
    skip_list_file = Path(__file__).parent / "skip_list.txt"

    # Read skip list
    skip_list = set()
    if skip_list_file.exists():
        with open(skip_list_file, "r") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith("#"):
                    skip_list.add(line)

    # Mark tests for skipping
    for item in items:
        # Get relative test path from tests/ directory
        test_path = Path(item.fspath).relative_to(Path(__file__).parent.parent)
        test_file = str(test_path).replace("\\", "/")  # Normalize path separators

        # Build test identifier
        if item.cls:
            test_id = f"{test_file}::{item.cls.__name__}::{item.name}"
        else:
            test_id = f"{test_file}::{item.name}"

        # Check if test should be skipped
        if test_id in skip_list:
            skip_marker = pytest.mark.skip(reason="Listed in skip_list.txt")
            item.add_marker(skip_marker)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "skip_from_list: mark test as skipped from skip_list.txt")
