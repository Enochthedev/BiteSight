"""Authentication utilities for JWT tokens and password hashing."""

from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, UUID], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return subject."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = payload.get("sub")
        if token_data is None:
            return None
        return token_data
    except (JWTError, ValidationError):
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_authentication_exception() -> HTTPException:
    """Create standardized authentication exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Security scheme for FastAPI
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current user (Student) object
        
    Raises:
        HTTPException: If authentication fails
    """
    from app.models.user import Student
    
    token = credentials.credentials
    user_id = verify_token(token)
    
    if user_id is None:
        raise create_authentication_exception()
    
    # Query user from database
    user = db.query(Student).filter(Student.id == user_id).first()
    
    if user is None:
        raise create_authentication_exception()
    
    return user
