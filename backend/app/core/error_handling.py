"""Comprehensive error handling and response formatting."""

import logging
import time
import traceback
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_ERROR = "internal_error"
    WORKFLOW_ERROR = "workflow_error"
    ML_ERROR = "ml_error"
    STORAGE_ERROR = "storage_error"


@dataclass
class ErrorDetail:
    """Detailed error information."""
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class StandardError:
    """Standardized error response format."""
    category: ErrorCategory
    code: str
    message: str
    details: List[ErrorDetail]
    timestamp: float
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    user_message: Optional[str] = None
    retry_after: Optional[int] = None
    help_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            "error": {
                "category": self.category.value,
                "code": self.code,
                "message": self.message,
                "timestamp": self.timestamp,
                "details": [
                    {
                        "code": detail.code,
                        "message": detail.message,
                        "field": detail.field,
                        "value": detail.value,
                        "context": detail.context
                    }
                    for detail in self.details
                ]
            }
        }

        # Add optional fields if present
        if self.request_id:
            result["error"]["request_id"] = self.request_id
        if self.trace_id:
            result["error"]["trace_id"] = self.trace_id
        if self.user_message:
            result["error"]["user_message"] = self.user_message
        if self.retry_after:
            result["error"]["retry_after"] = self.retry_after
        if self.help_url:
            result["error"]["help_url"] = self.help_url

        return result


class ErrorHandler:
    """Centralized error handling and response formatting."""

    def __init__(self):
        self.error_mappings = {
            # HTTP status codes to error categories
            400: ErrorCategory.VALIDATION,
            401: ErrorCategory.AUTHENTICATION,
            403: ErrorCategory.AUTHORIZATION,
            404: ErrorCategory.NOT_FOUND,
            409: ErrorCategory.CONFLICT,
            429: ErrorCategory.RATE_LIMIT,
            503: ErrorCategory.SERVICE_UNAVAILABLE,
            500: ErrorCategory.INTERNAL_ERROR
        }

    def create_error_response(
        self,
        category: ErrorCategory,
        code: str,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        status_code: int = 500,
        user_message: Optional[str] = None,
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Create a standardized error response."""

        error = StandardError(
            category=category,
            code=code,
            message=message,
            details=details or [],
            timestamp=time.time(),
            request_id=request_id,
            user_message=user_message,
            retry_after=retry_after
        )

        return JSONResponse(
            status_code=status_code,
            content=error.to_dict()
        )

    def handle_validation_error(
        self,
        errors: List[Dict[str, Any]],
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle validation errors from Pydantic."""

        details = []
        for error in errors:
            detail = ErrorDetail(
                code="VALIDATION_ERROR",
                message=error.get("msg", "Validation failed"),
                field=".".join(str(loc) for loc in error.get("loc", [])),
                value=error.get("input"),
                context={"type": error.get("type")}
            )
            details.append(detail)

        return self.create_error_response(
            category=ErrorCategory.VALIDATION,
            code="VALIDATION_FAILED",
            message="Request validation failed",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            user_message="Please check your input and try again",
            request_id=request_id
        )

    def handle_workflow_error(
        self,
        workflow_error: Exception,
        workflow_name: str,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle workflow execution errors."""

        from app.core.orchestration import WorkflowError

        if isinstance(workflow_error, WorkflowError):
            details = [
                ErrorDetail(
                    code="WORKFLOW_STEP_FAILED",
                    message=str(workflow_error),
                    field=workflow_error.step_name,
                    context={
                        "workflow": workflow_name,
                        "original_error": str(workflow_error.original_error) if workflow_error.original_error else None
                    }
                )
            ]

            return self.create_error_response(
                category=ErrorCategory.WORKFLOW_ERROR,
                code="WORKFLOW_EXECUTION_FAILED",
                message=f"Workflow '{workflow_name}' execution failed",
                details=details,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                user_message="The requested operation could not be completed. Please try again later.",
                request_id=request_id
            )
        else:
            return self.handle_internal_error(workflow_error, request_id)

    def handle_ml_error(
        self,
        ml_error: Exception,
        operation: str,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle machine learning related errors."""

        details = [
            ErrorDetail(
                code="ML_OPERATION_FAILED",
                message=str(ml_error),
                context={
                    "operation": operation,
                    "error_type": type(ml_error).__name__
                }
            )
        ]

        # Determine if this is a temporary or permanent error
        temporary_errors = ["TimeoutError",
                            "ConnectionError", "ResourceExhaustedError"]
        is_temporary = any(error_type in str(type(ml_error))
                           for error_type in temporary_errors)

        return self.create_error_response(
            category=ErrorCategory.ML_ERROR,
            code="ML_PROCESSING_FAILED",
            message=f"Machine learning operation '{operation}' failed",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE if is_temporary else status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="Image analysis is temporarily unavailable. Please try again in a few moments." if is_temporary else "Image analysis failed. Please try with a different image.",
            retry_after=30 if is_temporary else None,
            request_id=request_id
        )

    def handle_storage_error(
        self,
        storage_error: Exception,
        operation: str,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle file storage related errors."""

        details = [
            ErrorDetail(
                code="STORAGE_OPERATION_FAILED",
                message=str(storage_error),
                context={
                    "operation": operation,
                    "error_type": type(storage_error).__name__
                }
            )
        ]

        return self.create_error_response(
            category=ErrorCategory.STORAGE_ERROR,
            code="STORAGE_FAILED",
            message=f"Storage operation '{operation}' failed",
            details=details,
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            user_message="File storage is temporarily unavailable. Please try again later.",
            retry_after=60,
            request_id=request_id
        )

    def handle_rate_limit_error(
        self,
        limit: int,
        window: int,
        retry_after: int,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle rate limiting errors."""

        details = [
            ErrorDetail(
                code="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit of {limit} requests per {window} seconds exceeded",
                context={
                    "limit": limit,
                    "window": window,
                    "retry_after": retry_after
                }
            )
        ]

        return self.create_error_response(
            category=ErrorCategory.RATE_LIMIT,
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            user_message=f"You've made too many requests. Please wait {retry_after} seconds before trying again.",
            retry_after=retry_after,
            request_id=request_id
        )

    def handle_authentication_error(
        self,
        message: str = "Authentication required",
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle authentication errors."""

        details = [
            ErrorDetail(
                code="AUTHENTICATION_REQUIRED",
                message=message
            )
        ]

        return self.create_error_response(
            category=ErrorCategory.AUTHENTICATION,
            code="AUTHENTICATION_FAILED",
            message="Authentication required",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_message="Please log in to access this resource",
            request_id=request_id
        )

    def handle_authorization_error(
        self,
        resource: str,
        action: str,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle authorization errors."""

        details = [
            ErrorDetail(
                code="INSUFFICIENT_PERMISSIONS",
                message=f"Insufficient permissions to {action} {resource}",
                context={
                    "resource": resource,
                    "action": action
                }
            )
        ]

        return self.create_error_response(
            category=ErrorCategory.AUTHORIZATION,
            code="ACCESS_DENIED",
            message="Access denied",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
            user_message="You don't have permission to perform this action",
            request_id=request_id
        )

    def handle_not_found_error(
        self,
        resource: str,
        identifier: str,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Handle resource not found errors."""

        details = [
            ErrorDetail(
                code="RESOURCE_NOT_FOUND",
                message=f"{resource} with identifier '{identifier}' not found",
                context={
                    "resource": resource,
                    "identifier": identifier
                }
            )
        ]

        return self.create_error_response(
            category=ErrorCategory.NOT_FOUND,
            code="NOT_FOUND",
            message=f"{resource} not found",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
            user_message=f"The requested {resource.lower()} could not be found",
            request_id=request_id
        )

    def handle_internal_error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        include_traceback: bool = False
    ) -> JSONResponse:
        """Handle internal server errors."""

        # Log the full error for debugging
        logger.error(f"Internal error: {error}", exc_info=True)

        details = [
            ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                context={
                    "error_type": type(error).__name__,
                    "traceback": traceback.format_exc() if include_traceback else None
                }
            )
        ]

        return self.create_error_response(
            category=ErrorCategory.INTERNAL_ERROR,
            code="INTERNAL_ERROR",
            message="Internal server error",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="Something went wrong on our end. Please try again later.",
            request_id=request_id
        )


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Convenience functions for common error responses

def validation_error_response(
    errors: List[Dict[str, Any]],
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a validation error response."""
    return get_error_handler().handle_validation_error(errors, request_id)


def workflow_error_response(
    workflow_error: Exception,
    workflow_name: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a workflow error response."""
    return get_error_handler().handle_workflow_error(workflow_error, workflow_name, request_id)


def ml_error_response(
    ml_error: Exception,
    operation: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create an ML error response."""
    return get_error_handler().handle_ml_error(ml_error, operation, request_id)


def not_found_response(
    resource: str,
    identifier: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a not found error response."""
    return get_error_handler().handle_not_found_error(resource, identifier, request_id)


def internal_error_response(
    error: Exception,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create an internal error response."""
    return get_error_handler().handle_internal_error(error, request_id)
