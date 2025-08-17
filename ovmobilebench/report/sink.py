"""Report sinks for different output formats."""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ovmobilebench.core.fs import atomic_write, ensure_dir


class ReportSink(ABC):
    """Abstract base class for report sinks."""

    @abstractmethod
    def write(self, data: list[dict[str, Any]], path: Path):
        """Write data to sink."""
        pass


class JSONSink(ReportSink):
    """JSON format sink."""

    def write(self, data: list[dict[str, Any]], path: Path):
        """Write data as JSON."""
        ensure_dir(path.parent)
        content = json.dumps(data, indent=2, default=str)
        atomic_write(path, content)


class CSVSink(ReportSink):
    """CSV format sink."""

    def write(self, data: list[dict[str, Any]], path: Path):
        """Write data as CSV."""
        if not data:
            return

        ensure_dir(path.parent)

        # Flatten nested dictionaries
        flat_data = [self._flatten_dict(row) for row in data]

        # Get all field names
        fieldnames_set: set[str] = set()
        for row in flat_data:
            fieldnames_set.update(row.keys())
        fieldnames = sorted(fieldnames_set)

        # Write CSV
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_data)

    def _flatten_dict(self, d: dict[str, Any], parent_key: str = "") -> dict[str, Any]:
        """Flatten nested dictionary."""
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
