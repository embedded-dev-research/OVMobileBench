"""Tests for structured logging utilities."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

import pytest

from ovmobilebench.android.installer.logging import (
    StructuredLogger,
    get_logger,
    set_logger,
)


class TestStructuredLogger:
    """Test StructuredLogger class."""

    def test_init_basic(self):
        """Test basic logger initialization."""
        logger = StructuredLogger(name="test_logger")
        assert logger.name == "test_logger"
        assert logger.verbose is False
        assert logger.jsonl_path is None
        assert logger.jsonl_file is None

    def test_init_verbose(self):
        """Test verbose logger initialization."""
        logger = StructuredLogger(name="test_logger", verbose=True)
        assert logger.verbose is True
        assert logger.logger.level == logging.DEBUG

    def test_init_with_jsonl(self):
        """Test logger initialization with JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "log.jsonl"
            logger = StructuredLogger(name="test_logger", jsonl_path=jsonl_path)
            
            assert logger.jsonl_path == jsonl_path
            assert logger.jsonl_file is not None
            
            # Clean up
            logger.close()

    @patch("sys.stdout")
    def test_info_logging(self, mock_stdout):
        """Test info logging."""
        logger = StructuredLogger(name="test_logger")
        logger.info("Test message", key="value")
        
        # Check that message was logged
        assert logger.logger.hasHandlers()

    @patch("sys.stdout")
    def test_warning_logging(self, mock_stdout):
        """Test warning logging."""
        logger = StructuredLogger(name="test_logger")
        logger.warning("Warning message")
        
        # Warning should have emoji prefix
        assert logger.logger.hasHandlers()

    @patch("sys.stdout")
    def test_error_logging(self, mock_stdout):
        """Test error logging."""
        logger = StructuredLogger(name="test_logger")
        logger.error("Error message", error_code=1)
        
        # Error should have emoji prefix
        assert logger.logger.hasHandlers()

    @patch("sys.stdout")
    def test_debug_logging_verbose_off(self, mock_stdout):
        """Test debug logging when verbose is off."""
        logger = StructuredLogger(name="test_logger", verbose=False)
        logger.debug("Debug message")
        
        # Debug should not be visible when verbose is off
        assert logger.logger.level == logging.INFO

    @patch("sys.stdout")
    def test_debug_logging_verbose_on(self, mock_stdout):
        """Test debug logging when verbose is on."""
        logger = StructuredLogger(name="test_logger", verbose=True)
        logger.debug("Debug message")
        
        # Debug should be visible when verbose is on
        assert logger.logger.level == logging.DEBUG

    @patch("sys.stdout")
    def test_success_logging(self, mock_stdout):
        """Test success logging."""
        logger = StructuredLogger(name="test_logger")
        logger.success("Success message", result="ok")
        
        # Success should have emoji prefix
        assert logger.logger.hasHandlers()

    def test_jsonl_writing(self):
        """Test writing to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "log.jsonl"
            logger = StructuredLogger(name="test_logger", jsonl_path=jsonl_path)
            
            # Log some messages
            logger.info("Info message", data="test1")
            logger.warning("Warning message", data="test2")
            logger.error("Error message", data="test3")
            
            # Close logger to flush
            logger.close()
            
            # Read and verify JSONL file
            assert jsonl_path.exists()
            
            with open(jsonl_path, "r") as f:
                lines = f.readlines()
            
            assert len(lines) >= 3
            
            # Parse first line
            first_log = json.loads(lines[0])
            assert first_log["level"] == "INFO"
            assert first_log["message"] == "Info message"
            assert first_log["data"] == "test1"
            assert "timestamp" in first_log
            assert first_log["logger"] == "test_logger"

    @patch("sys.stdout")
    def test_step_context_success(self, mock_stdout):
        """Test step context manager with success."""
        logger = StructuredLogger(name="test_logger")
        
        with patch.object(logger, "info") as mock_info:
            with patch.object(logger, "success") as mock_success:
                with logger.step("test_step", param="value"):
                    # Simulate some work
                    time.sleep(0.01)
                
                # Check that info was called at start
                mock_info.assert_called()
                assert "Starting: test_step" in mock_info.call_args[0][0]
                
                # Check that success was called at end
                mock_success.assert_called()
                assert "Completed: test_step" in mock_success.call_args[0][0]

    @patch("sys.stdout")
    def test_step_context_failure(self, mock_stdout):
        """Test step context manager with failure."""
        logger = StructuredLogger(name="test_logger")
        
        with patch.object(logger, "info") as mock_info:
            with patch.object(logger, "error") as mock_error:
                with pytest.raises(ValueError, match="Test error"):
                    with logger.step("test_step"):
                        raise ValueError("Test error")
                
                # Check that error was called
                mock_error.assert_called()
                assert "Failed: test_step" in mock_error.call_args[0][0]

    def test_close(self):
        """Test closing logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "log.jsonl"
            logger = StructuredLogger(name="test_logger", jsonl_path=jsonl_path)
            
            assert logger.jsonl_file is not None
            
            logger.close()
            
            assert logger.jsonl_file is None

    def test_context_manager(self):
        """Test using logger as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "log.jsonl"
            
            with StructuredLogger(name="test_logger", jsonl_path=jsonl_path) as logger:
                assert logger.jsonl_file is not None
                logger.info("Test message")
            
            # File should be closed after context exit
            assert logger.jsonl_file is None


class TestLoggerFunctions:
    """Test module-level logger functions."""

    def test_get_logger_creates_new(self):
        """Test get_logger creates new logger."""
        # Reset global logger
        import ovmobilebench.android.installer.logging as log_module
        log_module._logger = None
        
        logger = get_logger(name="test", verbose=False)
        
        assert logger is not None
        assert logger.name == "test"
        assert logger.verbose is False

    def test_get_logger_returns_existing(self):
        """Test get_logger returns existing logger."""
        # Reset global logger
        import ovmobilebench.android.installer.logging as log_module
        log_module._logger = None
        
        logger1 = get_logger(name="test1", verbose=False)
        logger2 = get_logger(name="test2", verbose=False)
        
        # Should return same instance
        assert logger1 is logger2

    def test_get_logger_updates_verbosity(self):
        """Test get_logger updates verbosity if needed."""
        # Reset global logger
        import ovmobilebench.android.installer.logging as log_module
        log_module._logger = None
        
        logger1 = get_logger(name="test", verbose=False)
        assert logger1.verbose is False
        
        logger2 = get_logger(name="test", verbose=True)
        assert logger2 is logger1
        assert logger2.verbose is True

    def test_set_logger(self):
        """Test set_logger sets global logger."""
        # Reset global logger
        import ovmobilebench.android.installer.logging as log_module
        log_module._logger = None
        
        custom_logger = StructuredLogger(name="custom")
        set_logger(custom_logger)
        
        retrieved_logger = get_logger()
        assert retrieved_logger is custom_logger

    def test_logger_with_jsonl_path(self):
        """Test logger with JSONL path creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "nested" / "dir" / "log.jsonl"
            
            logger = StructuredLogger(name="test", jsonl_path=jsonl_path)
            
            # Parent directory should be created
            assert jsonl_path.parent.exists()
            
            logger.info("Test message")
            logger.close()
            
            # File should exist
            assert jsonl_path.exists()

    def test_jsonl_timestamp(self):
        """Test that JSONL entries have proper timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "log.jsonl"
            
            logger = StructuredLogger(name="test", jsonl_path=jsonl_path)
            
            start_time = time.time()
            logger.info("Test message")
            end_time = time.time()
            
            logger.close()
            
            # Read and check timestamp
            with open(jsonl_path, "r") as f:
                log_entry = json.loads(f.readline())
            
            assert "timestamp" in log_entry
            assert start_time <= log_entry["timestamp"] <= end_time

    def test_step_duration_tracking(self):
        """Test that step context tracks duration."""
        logger = StructuredLogger(name="test")
        
        with patch.object(logger, "success") as mock_success:
            with logger.step("test_step"):
                time.sleep(0.1)
            
            # Check that duration was tracked
            call_kwargs = mock_success.call_args[1]
            assert "duration" in call_kwargs
            assert call_kwargs["duration"] >= 0.1

    def test_logger_levels(self):
        """Test different logger levels in JSONL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = Path(tmpdir) / "log.jsonl"
            
            logger = StructuredLogger(name="test", jsonl_path=jsonl_path, verbose=True)
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.success("Success message")
            
            logger.close()
            
            # Read all log entries
            with open(jsonl_path, "r") as f:
                entries = [json.loads(line) for line in f]
            
            # Check levels
            levels = [entry["level"] for entry in entries]
            assert "DEBUG" in levels
            assert "INFO" in levels
            assert "WARNING" in levels
            assert "ERROR" in levels
            assert "SUCCESS" in levels