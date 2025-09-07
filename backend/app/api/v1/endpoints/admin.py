"""Admin authentication and management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.admin_dependencies import (
    get_current_admin_user, require_super_admin, require_user_management
)
from app.models.admin import (
    AdminUser, AdminUserCreate, AdminUserUpdate, AdminUserResponse,
    AdminLoginRequest, AdminLoginResponse
)
from app.services.admin_service import AdminService

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: Request,
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Admin user login."""
    admin_service = AdminService(db)

    # Authenticate admin
    admin_user = admin_service.authenticate_admin(login_data)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create session
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session = admin_service.create_admin_session(
        admin_user=admin_user,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Create login response
    return admin_service.create_login_response(admin_user, session)


@router.post("/logout")
async def admin_logout(
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin user logout."""
    admin_service = AdminService(db)

    # Logout all sessions for this admin
    success = admin_service.logout_admin(current_admin.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active sessions found"
        )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_profile(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Get current admin user profile."""
    return AdminUserResponse(
        id=current_admin.id,
        email=current_admin.email,
        name=current_admin.name,
        role=current_admin.role,
        is_active=current_admin.is_active,
        last_login=current_admin.last_login,
        created_at=current_admin.created_at,
        updated_at=current_admin.updated_at
    )


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    admin_data: AdminUserCreate,
    current_admin: AdminUser = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Create a new admin user. Requires super admin privileges."""
    admin_service = AdminService(db)

    try:
        admin_user = admin_service.create_admin_user(admin_data)
        return AdminUserResponse(
            id=admin_user.id,
            email=admin_user.email,
            name=admin_user.name,
            role=admin_user.role,
            is_active=admin_user.is_active,
            last_login=admin_user.last_login,
            created_at=admin_user.created_at,
            updated_at=admin_user.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )


@router.get("/users", response_model=List[AdminUserResponse])
async def list_admin_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: AdminUser = Depends(require_user_management),
    db: Session = Depends(get_db)
):
    """List all admin users."""
    admin_service = AdminService(db)

    admin_users = admin_service.list_admin_users(skip=skip, limit=limit)

    return [
        AdminUserResponse(
            id=admin.id,
            email=admin.email,
            name=admin.name,
            role=admin.role,
            is_active=admin.is_active,
            last_login=admin.last_login,
            created_at=admin.created_at,
            updated_at=admin.updated_at
        )
        for admin in admin_users
    ]


@router.get("/users/{admin_id}", response_model=AdminUserResponse)
async def get_admin_user(
    admin_id: str,
    current_admin: AdminUser = Depends(require_user_management),
    db: Session = Depends(get_db)
):
    """Get admin user by ID."""
    admin_service = AdminService(db)

    admin_user = admin_service.get_admin_by_id(admin_id)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )

    return AdminUserResponse(
        id=admin_user.id,
        email=admin_user.email,
        name=admin_user.name,
        role=admin_user.role,
        is_active=admin_user.is_active,
        last_login=admin_user.last_login,
        created_at=admin_user.created_at,
        updated_at=admin_user.updated_at
    )


@router.put("/users/{admin_id}", response_model=AdminUserResponse)
async def update_admin_user(
    admin_id: str,
    admin_data: AdminUserUpdate,
    current_admin: AdminUser = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Update admin user. Requires super admin privileges."""
    admin_service = AdminService(db)

    updated_admin = admin_service.update_admin_user(admin_id, admin_data)
    if not updated_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )

    return AdminUserResponse(
        id=updated_admin.id,
        email=updated_admin.email,
        name=updated_admin.name,
        role=updated_admin.role,
        is_active=updated_admin.is_active,
        last_login=updated_admin.last_login,
        created_at=updated_admin.created_at,
        updated_at=updated_admin.updated_at
    )


@router.delete("/users/{admin_id}")
async def delete_admin_user(
    admin_id: str,
    current_admin: AdminUser = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) admin user. Requires super admin privileges."""
    admin_service = AdminService(db)

    # Prevent self-deletion
    if str(current_admin.id) == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = admin_service.delete_admin_user(admin_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )

    return {"message": "Admin user successfully deactivated"}


@router.post("/cleanup-sessions")
async def cleanup_expired_sessions(
    current_admin: AdminUser = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Clean up expired admin sessions. Requires super admin privileges."""
    admin_service = AdminService(db)

    cleaned_count = admin_service.cleanup_expired_sessions()

    return {
        "message": f"Cleaned up {cleaned_count} expired sessions"
    }
