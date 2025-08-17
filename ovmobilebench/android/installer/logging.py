"""Structured logging utilities for Android installer."""

import json
import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredLogger:
    """Logger that outputs both human-readable and JSON-structured logs."""

    def __init__(
        self,
        name: str = "android_installer",
        verbose: bool = False,
        jsonl_path: Optional[Path] = None,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            verbose: Enable verbose output
            jsonl_path: Optional path to write JSON lines log
        """
        self.name = name
        self.verbose = verbose
        self.jsonl_path = jsonl_path
        self.jsonl_file = None

        # Setup standard logger for human-readable output
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

        # Simple format for console
        console_format = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # Open JSONL file if path provided
        if self.jsonl_path:
            self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            self.jsonl_file = open(self.jsonl_path, "a", encoding="utf-8")

    def _write_jsonl(self, record: Dict[str, Any]) -> None:
        """Write a record to JSONL file."""
        if self.jsonl_file:
            record["timestamp"] = time.time()
            record["logger"] = self.name
            json.dump(record, self.jsonl_file)
            self.jsonl_file.write("\n")
            self.jsonl_file.flush()

    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional structured data."""
        self.logger.info(message)
        if kwargs or self.jsonl_file:
            self._write_jsonl({"level": "INFO", "message": message, **kwargs})

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional structured data."""
        self.logger.warning(f"⚠️  {message}")
        if kwargs or self.jsonl_file:
            self._write_jsonl({"level": "WARNING", "message": message, **kwargs})

    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional structured data."""
        self.logger.error(f"❌ {message}")
        if kwargs or self.jsonl_file:
            self._write_jsonl({"level": "ERROR", "message": message, **kwargs})

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional structured data."""
        if self.verbose:
            self.logger.debug(f"[DEBUG] {message}")
        if kwargs or self.jsonl_file:
            self._write_jsonl({"level": "DEBUG", "message": message, **kwargs})

    def success(self, message: str, **kwargs) -> None:
        """Log success message with optional structured data."""
        self.logger.info(f"✅ {message}")
        if kwargs or self.jsonl_file:
            self._write_jsonl({"level": "SUCCESS", "message": message, **kwargs})

    @contextmanager
    def step(self, name: str, **kwargs):
        """Context manager for logging a step with timing."""
        start_time = time.time()
        self.info(f"Starting: {name}", step=name, start_time=start_time, **kwargs)

        try:
            yield self
        except Exception as e:
            duration = time.time() - start_time
            self.error(
                f"Failed: {name} ({duration:.2f}s)",
                step=name,
                duration=duration,
                error=str(e),
                **kwargs,
            )
            raise
        else:
            duration = time.time() - start_time
            self.success(
                f"Completed: {name} ({duration:.2f}s)",
                step=name,
                duration=duration,
                **kwargs,
            )

    def close(self) -> None:
        """Close the JSONL file if open."""
        if self.jsonl_file:
            self.jsonl_file.close()
            self.jsonl_file = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global logger instance
_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "android_installer",
    verbose: bool = False,
    jsonl_path: Optional[Path] = None,
) -> StructuredLogger:
    """Get or create the global logger instance.

    Args:
        name: Logger name
        verbose: Enable verbose output
        jsonl_path: Optional path to write JSON lines log

    Returns:
        StructuredLogger instance
    """
    global _logger
    if _logger is None:
        _logger = StructuredLogger(name=name, verbose=verbose, jsonl_path=jsonl_path)
    elif verbose and not _logger.verbose:
        # Update verbosity if requested
        _logger.verbose = verbose
        _logger.logger.setLevel(logging.DEBUG)
        for handler in _logger.logger.handlers:
            handler.setLevel(logging.DEBUG)
    return _logger


def set_logger(logger: StructuredLogger) -> None:
    """Set the global logger instance.

    Args:
        logger: Logger instance to use globally
    """
    global _logger
    _logger = logger