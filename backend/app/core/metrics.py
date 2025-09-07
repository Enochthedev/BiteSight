"""Metrics collection and monitoring for the application."""

import time
from typing import Dict, Optional, Any
from functools import wraps
from contextlib import contextmanager

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

from app.core.logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

ML_INFERENCE_COUNT = Counter(
    'ml_inference_requests_total',
    'Total ML inference requests',
    ['model_name', 'status']
)

ML_INFERENCE_DURATION = Histogram(
    'ml_inference_duration_seconds',
    'ML inference duration in seconds',
    ['model_name']
)

ML_INFERENCE_ERRORS = Counter(
    'ml_inference_errors_total',
    'Total ML inference errors',
    ['model_name', 'error_type']
)

DATABASE_QUERY_COUNT = Counter(
    'database_queries_total',
    'Total database queries',
    ['query_type', 'status']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

IMAGE_UPLOAD_COUNT = Counter(
    'image_uploads_total',
    'Total image uploads',
    ['status']
)

IMAGE_UPLOAD_FAILURES = Counter(
    'image_upload_failures_total',
    'Total image upload failures',
    ['error_type']
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

USER_REGISTRATIONS = Counter(
    'user_registrations_total',
    'Total user registrations'
)

FEEDBACK_GENERATED = Counter(
    'feedback_generated_total',
    'Total feedback messages generated',
    ['feedback_type']
)

# Application info
APP_INFO = Info(
    'nutrition_feedback_app',
    'Nutrition Feedback System application info'
)


class MetricsCollector:
    """Centralized metrics collection."""

    def __init__(self):
        self.start_time = time.time()
        self._cache_stats = {'hits': 0, 'misses': 0}

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint,
                             status=str(status_code)).inc()
        REQUEST_DURATION.labels(
            method=method, endpoint=endpoint).observe(duration)

        perf_logger.log_request(method, endpoint, status_code, duration)

    def record_ml_inference(self, model_name: str, duration: float, success: bool,
                            confidence: Optional[float] = None, error_type: Optional[str] = None):
        """Record ML inference metrics."""
        status = 'success' if success else 'error'
        ML_INFERENCE_COUNT.labels(model_name=model_name, status=status).inc()
        ML_INFERENCE_DURATION.labels(model_name=model_name).observe(duration)

        if not success and error_type:
            ML_INFERENCE_ERRORS.labels(
                model_name=model_name, error_type=error_type).inc()

        perf_logger.log_ml_inference(model_name, duration, success, confidence)

    def record_database_query(self, query_type: str, duration: float, success: bool,
                              rows_affected: Optional[int] = None):
        """Record database query metrics."""
        status = 'success' if success else 'error'
        DATABASE_QUERY_COUNT.labels(query_type=query_type, status=status).inc()
        DATABASE_QUERY_DURATION.labels(query_type=query_type).observe(duration)

        perf_logger.log_database_query(query_type, duration, rows_affected)

    def record_image_upload(self, success: bool, error_type: Optional[str] = None):
        """Record image upload metrics."""
        status = 'success' if success else 'error'
        IMAGE_UPLOAD_COUNT.labels(status=status).inc()

        if not success and error_type:
            IMAGE_UPLOAD_FAILURES.labels(error_type=error_type).inc()

    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics."""
        status = 'hit' if hit else 'miss'
        CACHE_OPERATIONS.labels(operation=operation, status=status).inc()

        # Update cache stats
        if hit:
            self._cache_stats['hits'] += 1
        else:
            self._cache_stats['misses'] += 1

        # Update hit rate
        total = self._cache_stats['hits'] + self._cache_stats['misses']
        if total > 0:
            hit_rate = (self._cache_stats['hits'] / total) * 100
            CACHE_HIT_RATE.set(hit_rate)

    def record_user_registration(self):
        """Record user registration."""
        USER_REGISTRATIONS.inc()

    def record_feedback_generated(self, feedback_type: str):
        """Record feedback generation."""
        FEEDBACK_GENERATED.labels(feedback_type=feedback_type).inc()

    def update_active_connections(self, count: int):
        """Update active connections count."""
        ACTIVE_CONNECTIONS.set(count)

    def set_app_info(self, version: str, environment: str):
        """Set application information."""
        APP_INFO.info({
            'version': version,
            'environment': environment,
            'start_time': str(self.start_time)
        })


# Global metrics collector instance
metrics = MetricsCollector()


def timed_operation(operation_name: str):
    """Decorator to time operations and record metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Operation {operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation {operation_name} failed after {duration:.3f}s: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Operation {operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation {operation_name} failed after {duration:.3f}s: {e}")
                raise

        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def measure_time(operation_name: str):
    """Context manager to measure operation time."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Operation {operation_name} took {duration:.3f}s")


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


class RequestMetricsMiddleware:
    """Middleware to collect request metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                method = scope["method"]
                path = scope["path"]
                status_code = message["status"]

                # Record metrics
                metrics.record_request(method, path, status_code, duration)

            await send(message)

        await self.app(scope, receive, send_wrapper)
