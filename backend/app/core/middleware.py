"""Custom middleware implementations."""

import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next):
        """Process request and log details."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {response.status_code} "
                f"for {request.method} {request.url.path} "
                f"in {process_time:.4f}s"
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} "
                f"for {request.method} {request.url.path} "
                f"in {process_time:.4f}s",
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting based on client IP."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests (older than 1 minute)
        minute_ago = current_time - 60
        while self.requests[client_ip] and self.requests[client_ip][0] < minute_ago:
            self.requests[client_ip].popleft()

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": 429,
                        "message": "Rate limit exceeded",
                        "type": "rate_limit_error",
                        "retry_after": 60
                    }
                }
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.requests_per_minute -
                        len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """Check request size before processing."""
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    f"Request size {content_length} exceeds limit {self.max_size} "
                    f"for {request.method} {request.url.path}"
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": {
                            "code": 413,
                            "message": f"Request size {content_length} exceeds maximum allowed size {self.max_size}",
                            "type": "request_too_large",
                            "max_size": self.max_size
                        }
                    }
                )

        return await call_next(request)


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check endpoints."""

    def __init__(self, app, health_endpoints: Optional[list] = None):
        super().__init__(app)
        self.health_endpoints = health_endpoints or [
            "/health", "/ping", "/status"]

    async def dispatch(self, request: Request, call_next):
        """Handle health check requests quickly."""
        if request.url.path in self.health_endpoints:
            # Skip other middleware for health checks
            return await call_next(request)

        return await call_next(request)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Middleware for setting cache control headers."""

    def __init__(self, app, static_paths: Optional[list] = None):
        super().__init__(app)
        self.static_paths = static_paths or ["/uploads", "/static"]

    async def dispatch(self, request: Request, call_next):
        """Add appropriate cache headers."""
        response = await call_next(request)

        # Set cache headers for static content
        for static_path in self.static_paths:
            if request.url.path.startswith(static_path):
                # 1 hour
                response.headers["Cache-Control"] = "public, max-age=3600"
                break
        else:
            # No cache for API endpoints
            if request.url.path.startswith("/api"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

        return response
