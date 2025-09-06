"""FastAPI dependencies for authentication and database access."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.auth import verify_token, create_authentication_exception
from app.core.database import get_db
from app.models.user import Student


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Student:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise create_authentication_exception()

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise create_authentication_exception()

    user = db.query(Student).filter(Student.id == user_uuid).first()
    if user is None:
        raise create_authentication_exception()

    return user


async def get_current_active_user(
    current_user: Student = Depends(get_current_user)
) -> Student:
    """Get current active user (can be extended for user status checks)."""
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Student]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        return None

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None

    user = db.query(Student).filter(Student.id == user_uuid).first()
    return user
