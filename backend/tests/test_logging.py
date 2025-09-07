"""Tests for logging configuration and functionality."""

import json
import logging
import tempfile
import os
from unittest.mock import patch, MagicMock

import pytest

from app.core.logging_config import (
    setup_logging, get_logger, get_performance_logger,
    JSONFormatter, PerformanceLogger
)


class TestJSONFormatter:
    """Test JSON formatter functionality."""

    def test_basic_formatting(self):
        """Test basic log record formatting."""
        formatter = JSONFormatter()

        # Create a test log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data

    def test_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"

        # Add extra fields
        record.user_id = "user123"
        record.request_id = "req456"
        record.duration = 0.123
        record.status_code = 200
        record.endpoint = "GET /api/test"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["user_id"] == "user123"
        assert log_data["request_id"] == "req456"
        assert log_data["duration"] == 0.123
        assert log_data["status_code"] == 200
        assert log_data["endpoint"] == "GET /api/test"

    def test_exception_formatting(self):
        """Test formatting with exception information."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            record.module = "test_module"
            record.funcName = "test_function"

            formatted = formatter.format(record)
            log_data = json.loads(formatted)

            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]
            assert "Test exception" in log_data["exception"]


class TestPerformanceLogger:
    """Test performance logger functionality."""

    def test_log_request(self):
        """Test logging API requests."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)

        perf_logger.log_request("GET", "/api/test", 200, 0.123, "user123")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "API Request: GET /api/test" in call_args[0][0]
        assert call_args[1]["extra"]["endpoint"] == "GET /api/test"
        assert call_args[1]["extra"]["status_code"] == 200
        assert call_args[1]["extra"]["duration"] == 0.123
        assert call_args[1]["extra"]["user_id"] == "user123"

    def test_log_ml_inference(self):
        """Test logging ML inference."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)

        perf_logger.log_ml_inference("mobilenet", 0.456, True, 0.95)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "ML Inference: mobilenet" in call_args[0][0]
        assert call_args[1]["extra"]["model_name"] == "mobilenet"
        assert call_args[1]["extra"]["duration"] == 0.456
        assert call_args[1]["extra"]["success"] is True
        assert call_args[1]["extra"]["confidence"] == 0.95

    def test_log_database_query(self):
        """Test logging database queries."""
        mock_logger = MagicMock()
        perf_logger = PerformanceLogger(mock_logger)

        perf_logger.log_database_query("SELECT", 0.089, 5)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        assert "Database Query: SELECT" in call_args[0][0]
        assert call_args[1]["extra"]["query_type"] == "SELECT"
        assert call_args[1]["extra"]["duration"] == 0.089
        assert call_args[1]["extra"]["rows_affected"] == 5


class TestLoggingSetup:
    """Test logging configuration setup."""

    def test_setup_logging(self):
        """Test logging setup function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for log files
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                setup_logging()

                # Check that logs directory was created
                assert os.path.exists("logs")

                # Test that loggers are configured
                logger = logging.getLogger("app.test")
                assert logger is not None

                # Test logging at different levels
                logger.debug("Debug message")
                logger.info("Info message")
                logger.warning("Warning message")
                logger.error("Error message")

                # Check that log files exist
                assert os.path.exists("logs/app.log")
                assert os.path.exists("logs/error.log")

            finally:
                os.chdir(original_cwd)

    def test_get_logger(self):
        """Test getting logger instances."""
        logger = get_logger("test_module")

        assert logger is not None
        assert logger.name == "app.test_module"
        assert isinstance(logger, logging.Logger)

    def test_get_performance_logger(self):
        """Test getting performance logger instances."""
        perf_logger = get_performance_logger("test_module")

        assert perf_logger is not None
        assert isinstance(perf_logger, PerformanceLogger)
        assert perf_logger.logger.name == "app.test_module"


class TestLoggingIntegration:
    """Test logging integration with application components."""

    def test_structured_logging_format(self):
        """Test that structured logging produces valid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                setup_logging()
                logger = get_logger("test")

                # Log a message with extra fields
                logger.info(
                    "Test structured log",
                    extra={
                        "user_id": "user123",
                        "request_id": "req456",
                        "endpoint": "GET /api/test"
                    }
                )

                # Read the log file and verify JSON format
                with open("logs/app.log", "r") as f:
                    log_content = f.read()

                # Should contain structured log entry
                assert "Test structured log" in log_content

            finally:
                os.chdir(original_cwd)

    def test_error_logging_with_traceback(self):
        """Test error logging with exception traceback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                setup_logging()
                logger = get_logger("test")

                # Log an exception
                try:
                    raise ValueError("Test exception for logging")
                except ValueError:
                    logger.exception("An error occurred during testing")

                # Read the error log file
                with open("logs/error.log", "r") as f:
                    error_content = f.read()

                # Should contain exception information
                assert "An error occurred during testing" in error_content
                assert "ValueError" in error_content
                assert "Test exception for logging" in error_content

            finally:
                os.chdir(original_cwd)

    @patch('app.core.config.settings')
    def test_debug_mode_logging(self, mock_settings):
        """Test logging configuration in debug mode."""
        mock_settings.DEBUG = True

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                setup_logging()

                # In debug mode, root logger should be set to DEBUG level
                root_logger = logging.getLogger()
                assert root_logger.level == logging.DEBUG

            finally:
                os.chdir(original_cwd)

    @patch('app.core.config.settings')
    def test_production_mode_logging(self, mock_settings):
        """Test logging configuration in production mode."""
        mock_settings.DEBUG = False

        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                setup_logging()

                # In production mode, root logger should be set to INFO level
                root_logger = logging.getLogger()
                assert root_logger.level == logging.INFO

            finally:
                os.chdir(original_cwd)


class TestLogRotation:
    """Test log rotation functionality."""

    def test_log_file_rotation_config(self):
        """Test that log rotation is properly configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                setup_logging()

                # Get the file handler
                app_logger = logging.getLogger("app")
                file_handlers = [
                    handler for handler in app_logger.handlers
                    if isinstance(handler, logging.handlers.RotatingFileHandler)
                ]

                assert len(file_handlers) > 0

                # Check rotation settings
                for handler in file_handlers:
                    assert handler.maxBytes == 10485760  # 10MB
                    assert handler.backupCount == 5

            finally:
                os.chdir(original_cwd)
