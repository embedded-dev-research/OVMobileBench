"""Report sinks for different output formats."""

import json
import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any

from ovmobilebench.core.fs import ensure_dir, atomic_write


class ReportSink(ABC):
    """Abstract base class for report sinks."""

    @abstractmethod
    def write(self, data: List[Dict[str, Any]], path: Path):
        """Write data to sink."""
        pass


class JSONSink(ReportSink):
    """JSON format sink."""

    def write(self, data: List[Dict[str, Any]], path: Path):
        """Write data as JSON."""
        ensure_dir(path.parent)
        content = json.dumps(data, indent=2, default=str)
        atomic_write(path, content)


class CSVSink(ReportSink):
    """CSV format sink."""

    def write(self, data: List[Dict[str, Any]], path: Path):
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

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items: List[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
