"""Consent verification middleware."""

from typing import List, Optional
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Student
from app.services.consent_service import ConsentService


class ConsentRequiredError(HTTPException):
    """Exception raised when required consent is missing."""

    def __init__(self, missing_consents: List[str]):
        detail = {
            "error": "consent_required",
            "message": "Required consent not given",
            "missing_consents": missing_consents,
            "action_required": "Please update your consent preferences"
        }
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def require_consent(required_consents: List[str]):
    """
    Dependency factory that creates a consent verification dependency.

    Args:
        required_consents: List of consent types required (e.g., ['data_processing', 'history_storage'])

    Returns:
        FastAPI dependency function
    """
    def consent_dependency(
        current_user: Student = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> Student:
        """Verify that the current user has given required consents."""
        consent_service = ConsentService(db)

        verification_result = consent_service.verify_consent(
            current_user.id,
            required_consents
        )

        if verification_result.requires_update:
            raise ConsentRequiredError(verification_result.missing_consents)

        return current_user

    return consent_dependency


def require_data_processing_consent():
    """Dependency that requires data processing consent."""
    return require_consent(["data_processing"])


def require_history_storage_consent():
    """Dependency that requires history storage consent."""
    return require_consent(["data_processing", "history_storage"])


def require_analytics_consent():
    """Dependency that requires analytics consent."""
    return require_consent(["data_processing", "analytics"])


def require_all_consents():
    """Dependency that requires all consent types."""
    return require_consent(["data_processing", "history_storage", "analytics"])


class ConsentMiddleware:
    """Middleware for automatic consent checking on specific routes."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation."""
        # This could be extended to automatically check consent for certain routes
        # For now, we'll use the dependency approach which is more explicit
        await self.app(scope, receive, send)
