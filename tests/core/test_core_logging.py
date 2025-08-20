"""Tests for core.logging module."""

import json
import logging
import tempfile
from pathlib import Path

from ovmobilebench.core.logging import JSONFormatter, get_logger, setup_logging


class TestJSONFormatter:
    """Test JSONFormatter class."""

    def test_format_basic(self):
        """Test basic formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "Test error" in data["exception"]

    def test_format_with_extra(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra = {"user_id": 123, "action": "test"}

        result = formatter.format(record)
        data = json.loads(result)

        assert data["user_id"] == 123
        assert data["action"] == "test"


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_basic(self):
        """Test basic logging setup."""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(level="INFO")

        assert len(root_logger.handlers) > 0
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)
        assert root_logger.level == logging.INFO

    def test_setup_with_debug_level(self):
        """Test setup with DEBUG level."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(level="DEBUG")

        assert root_logger.level == logging.DEBUG

    def test_setup_with_invalid_level(self):
        """Test setup with invalid level defaults to INFO."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(level="INVALID")

        assert root_logger.level == logging.INFO

    def test_setup_with_file_handler(self):
        """Test setup with file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            root_logger = logging.getLogger()
            root_logger.handlers.clear()

            setup_logging(level="INFO", log_file=log_file)

            # Should have both console and file handlers
            assert len(root_logger.handlers) >= 2

            # Test that file handler works
            test_logger = logging.getLogger("test")
            test_logger.info("Test message")

            # File should be created
            assert log_file.exists()

            # Clean up handlers to release file lock
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)

    def test_setup_with_json_format(self):
        """Test setup with JSON format."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        setup_logging(level="INFO", json_format=True)

        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_setup_with_file_and_json(self):
        """Test setup with both file and JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            root_logger = logging.getLogger()
            root_logger.handlers.clear()

            setup_logging(level="INFO", log_file=log_file, json_format=True)

            # Console handler should have JSON formatter
            console_handler = root_logger.handlers[0]
            assert isinstance(console_handler.formatter, JSONFormatter)

            # File handler should also have JSON formatter
            file_handler = root_logger.handlers[1]
            assert isinstance(file_handler.formatter, JSONFormatter)

            # Clean up handlers to release file lock
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger(self):
        """Test get_logger returns correct logger."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_multiple(self):
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")

        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """Test get_logger returns different instances for different names."""
        logger1 = get_logger("test.module1")
        logger2 = get_logger("test.module2")

        assert logger1 is not logger2
        assert logger1.name == "test.module1"
        assert logger2.name == "test.module2"
