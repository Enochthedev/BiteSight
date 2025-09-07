"""Admin user management service."""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.auth import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.admin import (
    AdminUser, AdminPermission, AdminRolePermission, AdminSession,
    AdminUserCreate, AdminUserUpdate, AdminLoginRequest, AdminLoginResponse,
    AdminUserResponse, AdminRole
)


class AdminService:
    """Service for admin user management and authentication."""

    def __init__(self, db: Session):
        self.db = db

    def create_admin_user(self, admin_data: AdminUserCreate) -> AdminUser:
        """Create a new admin user."""
        # Check if email already exists
        existing_admin = self.db.query(AdminUser).filter(
            AdminUser.email == admin_data.email
        ).first()

        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new admin user
        admin_user = AdminUser(
            email=admin_data.email,
            name=admin_data.name,
            password_hash=get_password_hash(admin_data.password),
            role=admin_data.role.value,
            is_active=True
        )

        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)

        return admin_user

    def authenticate_admin(self, login_data: AdminLoginRequest) -> Optional[AdminUser]:
        """Authenticate admin user."""
        admin_user = self.db.query(AdminUser).filter(
            and_(
                AdminUser.email == login_data.email,
                AdminUser.is_active == True
            )
        ).first()

        if not admin_user or not verify_password(login_data.password, admin_user.password_hash):
            return None

        # Update last login
        admin_user.last_login = datetime.utcnow()
        self.db.commit()

        return admin_user

    def get_admin_permissions(self, admin_user: AdminUser) -> List[str]:
        """Get all permissions for an admin user based on their role."""
        permissions = self.db.query(AdminPermission).join(
            AdminRolePermission,
            AdminPermission.id == AdminRolePermission.permission_id
        ).filter(
            AdminRolePermission.role == admin_user.role
        ).all()

        return [f"{perm.resource}:{perm.action}" for perm in permissions]

    def create_admin_session(self, admin_user: AdminUser, ip_address: str = None, user_agent: str = None) -> AdminSession:
        """Create a new admin session."""
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=settings.ADMIN_SESSION_EXPIRE_HOURS)

        # Deactivate old sessions for this user
        self.db.query(AdminSession).filter(
            and_(
                AdminSession.admin_user_id == admin_user.id,
                AdminSession.is_active == True
            )
        ).update({"is_active": False})

        # Create new session
        session = AdminSession(
            admin_user_id=admin_user.id,
            session_token=session_token,
            expires_at=expires_at,
            is_active=True,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def create_login_response(self, admin_user: AdminUser, session: AdminSession) -> AdminLoginResponse:
        """Create admin login response with token and permissions."""
        # Create JWT token
        access_token = create_access_token(
            subject=str(admin_user.id),
            expires_delta=timedelta(hours=settings.ADMIN_SESSION_EXPIRE_HOURS)
        )

        # Get user permissions
        permissions = self.get_admin_permissions(admin_user)

        return AdminLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ADMIN_SESSION_EXPIRE_HOURS * 3600,
            admin_user=AdminUserResponse(
                id=admin_user.id,
                email=admin_user.email,
                name=admin_user.name,
                role=admin_user.role,
                is_active=admin_user.is_active,
                last_login=admin_user.last_login,
                created_at=admin_user.created_at,
                updated_at=admin_user.updated_at
            ),
            permissions=permissions
        )

    def get_admin_by_id(self, admin_id: UUID) -> Optional[AdminUser]:
        """Get admin user by ID."""
        return self.db.query(AdminUser).filter(
            and_(
                AdminUser.id == admin_id,
                AdminUser.is_active == True
            )
        ).first()

    def get_admin_by_email(self, email: str) -> Optional[AdminUser]:
        """Get admin user by email."""
        return self.db.query(AdminUser).filter(
            and_(
                AdminUser.email == email,
                AdminUser.is_active == True
            )
        ).first()

    def update_admin_user(self, admin_id: UUID, admin_data: AdminUserUpdate) -> Optional[AdminUser]:
        """Update admin user."""
        admin_user = self.get_admin_by_id(admin_id)
        if not admin_user:
            return None

        # Update fields
        if admin_data.name is not None:
            admin_user.name = admin_data.name
        if admin_data.role is not None:
            admin_user.role = admin_data.role.value
        if admin_data.is_active is not None:
            admin_user.is_active = admin_data.is_active

        admin_user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(admin_user)

        return admin_user

    def delete_admin_user(self, admin_id: UUID) -> bool:
        """Soft delete admin user by deactivating."""
        admin_user = self.get_admin_by_id(admin_id)
        if not admin_user:
            return False

        admin_user.is_active = False
        admin_user.updated_at = datetime.utcnow()

        # Deactivate all sessions
        self.db.query(AdminSession).filter(
            AdminSession.admin_user_id == admin_id
        ).update({"is_active": False})

        self.db.commit()
        return True

    def validate_session(self, session_token: str) -> Optional[AdminUser]:
        """Validate admin session token."""
        session = self.db.query(AdminSession).filter(
            and_(
                AdminSession.session_token == session_token,
                AdminSession.is_active == True,
                AdminSession.expires_at > datetime.utcnow()
            )
        ).first()

        if not session:
            return None

        return session.admin_user

    def logout_admin(self, admin_id: UUID, session_token: str = None) -> bool:
        """Logout admin user by deactivating sessions."""
        query = self.db.query(AdminSession).filter(
            and_(
                AdminSession.admin_user_id == admin_id,
                AdminSession.is_active == True
            )
        )

        if session_token:
            # Logout specific session
            query = query.filter(AdminSession.session_token == session_token)

        sessions_updated = query.update({"is_active": False})
        self.db.commit()

        return sessions_updated > 0

    def has_permission(self, admin_user: AdminUser, resource: str, action: str) -> bool:
        """Check if admin user has specific permission."""
        # Super admin has all permissions
        if admin_user.role == AdminRole.SUPER_ADMIN.value:
            return True

        # Check specific permission
        permission_exists = self.db.query(AdminPermission).join(
            AdminRolePermission,
            AdminPermission.id == AdminRolePermission.permission_id
        ).filter(
            and_(
                AdminRolePermission.role == admin_user.role,
                AdminPermission.resource == resource,
                AdminPermission.action == action
            )
        ).first()

        return permission_exists is not None

    def list_admin_users(self, skip: int = 0, limit: int = 100) -> List[AdminUser]:
        """List all admin users."""
        return self.db.query(AdminUser).filter(
            AdminUser.is_active == True
        ).offset(skip).limit(limit).all()

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired admin sessions."""
        expired_count = self.db.query(AdminSession).filter(
            and_(
                AdminSession.is_active == True,
                AdminSession.expires_at <= datetime.utcnow()
            )
        ).update({"is_active": False})

        self.db.commit()
        return expired_count
