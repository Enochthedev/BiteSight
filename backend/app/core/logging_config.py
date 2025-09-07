"""Logging configuration for the application."""

import json
import logging
import logging.config
import sys
import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings


def setup_logging() -> None:
    """Setup application logging configuration."""

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "app.core.logging_config.JSONFormatter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }

    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)

    # Apply logging configuration
    logging.config.dictConfig(logging_config)

    # Set log level based on environment
    if settings.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class PerformanceLogger:
    """Logger for performance metrics and timing."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_request(self, method: str, path: str, status_code: int,
                    duration: float, user_id: Optional[str] = None):
        """Log API request performance."""
        self.logger.info(
            f"API Request: {method} {path}",
            extra={
                'endpoint': f"{method} {path}",
                'status_code': status_code,
                'duration': duration,
                'user_id': user_id
            }
        )

    def log_ml_inference(self, model_name: str, duration: float,
                         success: bool, confidence: Optional[float] = None):
        """Log ML inference performance."""
        self.logger.info(
            f"ML Inference: {model_name}",
            extra={
                'model_name': model_name,
                'duration': duration,
                'success': success,
                'confidence': confidence
            }
        )

    def log_database_query(self, query_type: str, duration: float,
                           rows_affected: Optional[int] = None):
        """Log database query performance."""
        self.logger.info(
            f"Database Query: {query_type}",
            extra={
                'query_type': query_type,
                'duration': duration,
                'rows_affected': rows_affected
            }
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"app.{name}")


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger instance."""
    logger = get_logger(name)
    return PerformanceLogger(logger)
