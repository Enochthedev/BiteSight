"""User service for authentication and user management operations."""

from datetime import timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.auth import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import Student, StudentCreate, StudentUpdate, LoginRequest, LoginResponse, StudentResponse


class UserService:
    """Service class for user operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: StudentCreate) -> Student:
        """Create a new user account."""
        # Check if user already exists
        existing_user = self.db.query(Student).filter(
            Student.email == user_data.email
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = Student(
            email=user_data.email,
            name=user_data.name,
            password_hash=hashed_password,
            history_enabled=False  # Default to disabled for privacy
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def authenticate_user(self, login_data: LoginRequest) -> Optional[Student]:
        """Authenticate user with email and password."""
        user = self.db.query(Student).filter(
            Student.email == login_data.email
        ).first()

        if not user:
            return None

        if not verify_password(login_data.password, user.password_hash):
            return None

        return user

    def create_login_response(self, user: Student) -> LoginResponse:
        """Create login response with access token."""
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            student=StudentResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                registration_date=user.registration_date,
                history_enabled=user.history_enabled,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )

    def get_user_by_id(self, user_id: UUID) -> Optional[Student]:
        """Get user by ID."""
        return self.db.query(Student).filter(Student.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[Student]:
        """Get user by email."""
        return self.db.query(Student).filter(Student.email == email).first()

    def update_user(self, user_id: UUID, user_data: StudentUpdate) -> Optional[Student]:
        """Update user profile."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(self, user_id: UUID) -> bool:
        """Delete user account and all associated data."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()

        return True
