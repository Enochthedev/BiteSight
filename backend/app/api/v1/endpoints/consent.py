"""Consent management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Student
from app.models.consent import (
    ConsentRequest, ConsentResponse, ConsentUpdateRequest,
    ConsentHistoryResponse, ConsentVerificationResult
)
from app.services.consent_service import ConsentService

router = APIRouter()


@router.post("/", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_consent(
    consent_data: ConsentRequest,
    request: Request,
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record user consent preferences."""
    consent_service = ConsentService(db)

    try:
        return consent_service.record_consent(
            current_user.id,
            consent_data,
            request
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent"
        )


@router.get("/", response_model=ConsentResponse)
async def get_current_consent(
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current consent status for the authenticated user."""
    consent_service = ConsentService(db)
    return consent_service.get_current_consent(current_user.id)


@router.put("/", response_model=ConsentResponse)
async def update_consent(
    consent_updates: ConsentUpdateRequest,
    request: Request,
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update specific consent preferences."""
    consent_service = ConsentService(db)

    try:
        return consent_service.update_consent(
            current_user.id,
            consent_updates,
            request
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update consent"
        )


@router.post("/verify", response_model=ConsentVerificationResult)
async def verify_consent(
    required_consents: List[str],
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify that user has given required consents."""
    consent_service = ConsentService(db)

    # Validate consent types
    valid_consent_types = ["data_processing", "history_storage", "analytics"]
    invalid_types = [
        ct for ct in required_consents if ct not in valid_consent_types]

    if invalid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid consent types: {invalid_types}"
        )

    return consent_service.verify_consent(current_user.id, required_consents)


@router.get("/history", response_model=List[ConsentHistoryResponse])
async def get_consent_history(
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consent history for the authenticated user."""
    consent_service = ConsentService(db)
    return consent_service.get_consent_history(current_user.id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_consents(
    request: Request,
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke all consents (for data deletion requests)."""
    consent_service = ConsentService(db)

    success = consent_service.revoke_all_consents(current_user.id, request)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke consents"
        )

    return {"message": "All consents revoked successfully"}


@router.get("/required/{endpoint_path:path}", response_model=List[str])
async def get_required_consents_for_endpoint(endpoint_path: str):
    """Get required consent types for a specific endpoint (for frontend guidance)."""
    # This is a helper endpoint to inform the frontend about consent requirements
    # In a real implementation, this could be dynamically determined

    consent_requirements = {
        "meals/upload": ["data_processing"],
        "meals/history": ["data_processing", "history_storage"],
        "insights/weekly": ["data_processing", "history_storage"],
        "analytics/": ["data_processing", "analytics"],
    }

    # Find matching requirement
    for path_pattern, required_consents in consent_requirements.items():
        if endpoint_path.startswith(path_pattern):
            return required_consents

    # Default to data processing consent for most endpoints
    return ["data_processing"]
