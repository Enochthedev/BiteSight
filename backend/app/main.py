"""Main FastAPI application."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging_config import setup_logging
from app.core.api_docs import setup_api_docs
from app.core.middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestSizeMiddleware
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Nutrition Feedback API...")

    # Initialize database connection
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    # Initialize async task processor
    try:
        from app.core.async_tasks import get_task_processor
        task_processor = await get_task_processor()
        logger.info("Async task processor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize async task processor: {e}")
        raise

    # Initialize service orchestrator
    try:
        from app.core.orchestration import get_orchestrator
        orchestrator = get_orchestrator()
        logger.info("Service orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize service orchestrator: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Nutrition Feedback API...")

    # Cleanup async task processor
    try:
        task_processor = await get_task_processor()
        await task_processor.stop()
        logger.info("Async task processor stopped")
    except Exception as e:
        logger.error(f"Error stopping async task processor: {e}")

    # Cleanup orchestrator
    try:
        orchestrator = get_orchestrator()
        orchestrator.cleanup_completed_tasks(0)  # Clean all tasks
        logger.info("Service orchestrator cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up orchestrator: {e}")


app = FastAPI(
    title="Nutrition Feedback API",
    description="AI-Powered Visual Nutrition Feedback System for Nigerian Students",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(SecurityHeadersMiddleware)

# Request processing middleware
app.add_middleware(RequestSizeMiddleware, max_size=settings.MAX_UPLOAD_SIZE)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    from app.core.error_handling import get_error_handler

    # Get request ID from headers if available
    request_id = request.headers.get("X-Request-ID")

    error_handler = get_error_handler()
    return error_handler.handle_validation_error(exc.errors(), request_id)


@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "server_error",
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    from app.core.error_handling import get_error_handler

    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Get request ID from headers if available
    request_id = request.headers.get("X-Request-ID")

    error_handler = get_error_handler()
    return error_handler.handle_internal_error(exc, request_id)


# Setup API documentation
setup_api_docs(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Nutrition Feedback API",
        "version": "1.0.0",
        "status": "healthy",
        "docs_url": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "nutrition-feedback-api",
        "version": "1.0.0",
        "timestamp": time.time(),
        "components": {
            "database": db_status,
            "api": "healthy"
        }
    }
