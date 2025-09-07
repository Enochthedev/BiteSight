"""Admin authentication and authorization dependencies."""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_token
from app.models.admin import AdminUser
from app.services.admin_service import AdminService


# HTTP Bearer token scheme for admin authentication
admin_security = HTTPBearer(scheme_name="Admin Bearer")


async def get_current_admin_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(admin_security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get current authenticated admin user."""

    # Verify JWT token
    admin_id = verify_token(credentials.credentials)
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get admin user from database
    admin_service = AdminService(db)
    admin_user = admin_service.get_admin_by_id(admin_id)

    if not admin_user or not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin_user


def require_admin_permission(resource: str, action: str):
    """Dependency factory for requiring specific admin permissions."""

    def permission_dependency(
        current_admin: AdminUser = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
    ) -> AdminUser:
        """Check if current admin has required permission."""

        admin_service = AdminService(db)

        if not admin_service.has_permission(current_admin, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {resource}:{action}"
            )

        return current_admin

    return permission_dependency


def require_super_admin(
    current_admin: AdminUser = Depends(get_current_admin_user)
) -> AdminUser:
    """Require super admin role."""

    if current_admin.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )

    return current_admin


def require_admin_role(*allowed_roles: str):
    """Dependency factory for requiring specific admin roles."""

    def role_dependency(
        current_admin: AdminUser = Depends(get_current_admin_user)
    ) -> AdminUser:
        """Check if current admin has required role."""

        if current_admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(allowed_roles)}"
            )

        return current_admin

    return role_dependency


# Common permission dependencies
require_dataset_management = require_admin_permission("dataset", "manage")
require_nutrition_rules_management = require_admin_permission(
    "nutrition_rules", "manage")
require_user_management = require_admin_permission("users", "manage")
require_system_administration = require_admin_permission("system", "admin")

# Common role dependencies
require_nutritionist_or_admin = require_admin_role(
    "nutritionist", "admin", "super_admin")
require_dataset_manager_or_admin = require_admin_role(
    "dataset_manager", "admin", "super_admin")
