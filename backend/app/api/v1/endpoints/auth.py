"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import (
    Student, StudentCreate, StudentUpdate, StudentResponse,
    LoginRequest, LoginResponse
)
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: StudentCreate,
    db: Session = Depends(get_db)
):
    """Register a new student."""
    user_service = UserService(db)

    try:
        user = user_service.create_user(user_data)
        return StudentResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            registration_date=user.registration_date,
            history_enabled=user.history_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Student login."""
    user_service = UserService(db)

    user = user_service.authenticate_user(login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_service.create_login_response(user)


@router.post("/logout")
async def logout(
    current_user: Student = Depends(get_current_user)
):
    """Student logout."""
    # JWT tokens are stateless, so logout is handled client-side
    # This endpoint can be used for logging purposes or token blacklisting if needed
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=StudentResponse)
async def get_current_user_profile(
    current_user: Student = Depends(get_current_user)
):
    """Get current user profile."""
    return StudentResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        registration_date=current_user.registration_date,
        history_enabled=current_user.history_enabled,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/me", response_model=StudentResponse)
async def update_current_user_profile(
    user_data: StudentUpdate,
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    user_service = UserService(db)

    updated_user = user_service.update_user(current_user.id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return StudentResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        registration_date=updated_user.registration_date,
        history_enabled=updated_user.history_enabled,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )


@router.delete("/me")
async def delete_current_user_account(
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account and all associated data."""
    user_service = UserService(db)

    success = user_service.delete_user(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": "Account successfully deleted"}
