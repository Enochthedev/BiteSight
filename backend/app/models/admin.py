"""Admin users, role-based permissions and sessions (migration 003)."""

import enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, func

from sqlalchemy.orm import relationship

from .base import UUID, Base, TimestampMixin, uuid_pk


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    NUTRITIONIST = "nutritionist"
    DATASET_MANAGER = "dataset_manager"


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"
    __table_args__ = (Index("ix_admin_users_email", "email"),)

    id = uuid_pk()
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=AdminRole.ADMIN.value, index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime(timezone=True))

    sessions = relationship("AdminSession", back_populates="admin_user", cascade="all, delete-orphan")


class AdminPermission(Base):
    __tablename__ = "admin_permissions"
    __table_args__ = (Index("ix_admin_permissions_name", "name"),)

    id = uuid_pk()
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    resource = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdminRolePermission(Base):
    __tablename__ = "admin_role_permissions"
    __table_args__ = (
        Index("ix_admin_role_permissions_unique", "role", "permission_id", unique=True),
    )

    id = uuid_pk()
    role = Column(String(50), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("admin_permissions.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    permission = relationship("AdminPermission")


class AdminSession(Base):
    __tablename__ = "admin_sessions"
    __table_args__ = (Index("ix_admin_sessions_session_token", "session_token"),)

    id = uuid_pk()
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin_user = relationship("AdminUser", back_populates="sessions")


class AdminUserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    role: AdminRole = AdminRole.ADMIN


class AdminUserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[AdminRole] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PyUUID
    email: EmailStr
    name: str
    role: str
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_user: AdminUserResponse
    permissions: List[str] = []
