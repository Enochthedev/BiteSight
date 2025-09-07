"""Tests for admin authentication and authorization."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.admin import AdminUser, AdminRole
from app.services.admin_service import AdminService
from app.core.auth import get_password_hash


@pytest.fixture
def admin_service(db_session: Session):
    """Create admin service instance."""
    return AdminService(db_session)


@pytest.fixture
def test_admin_user(db_session: Session):
    """Create a test admin user."""
    admin_user = AdminUser(
        email="admin@test.com",
        name="Test Admin",
        password_hash=get_password_hash("testpassword123"),
        role=AdminRole.ADMIN.value,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def test_super_admin_user(db_session: Session):
    """Create a test super admin user."""
    admin_user = AdminUser(
        email="superadmin@test.com",
        name="Test Super Admin",
        password_hash=get_password_hash("superpassword123"),
        role=AdminRole.SUPER_ADMIN.value,
        is_active=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAdminAuthentication:
    """Test admin authentication functionality."""

    def test_create_admin_user(self, admin_service: AdminService):
        """Test creating a new admin user."""
        from app.models.admin import AdminUserCreate

        admin_data = AdminUserCreate(
            email="newadmin@test.com",
            name="New Admin",
            password="newpassword123",
            role=AdminRole.ADMIN
        )

        admin_user = admin_service.create_admin_user(admin_data)

        assert admin_user.email == "newadmin@test.com"
        assert admin_user.name == "New Admin"
        assert admin_user.role == AdminRole.ADMIN.value
        assert admin_user.is_active is True
        assert admin_user.password_hash != "newpassword123"  # Should be hashed

    def test_create_duplicate_admin_user(self, admin_service: AdminService, test_admin_user):
        """Test creating admin user with duplicate email."""
        from app.models.admin import AdminUserCreate
        from fastapi import HTTPException

        admin_data = AdminUserCreate(
            email=test_admin_user.email,
            name="Duplicate Admin",
            password="password123",
            role=AdminRole.ADMIN
        )

        with pytest.raises(HTTPException) as exc_info:
            admin_service.create_admin_user(admin_data)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    def test_authenticate_admin_success(self, admin_service: AdminService, test_admin_user):
        """Test successful admin authentication."""
        from app.models.admin import AdminLoginRequest

        login_data = AdminLoginRequest(
            email=test_admin_user.email,
            password="testpassword123"
        )

        authenticated_admin = admin_service.authenticate_admin(login_data)

        assert authenticated_admin is not None
        assert authenticated_admin.id == test_admin_user.id
        assert authenticated_admin.email == test_admin_user.email

    def test_authenticate_admin_wrong_password(self, admin_service: AdminService, test_admin_user):
        """Test admin authentication with wrong password."""
        from app.models.admin import AdminLoginRequest

        login_data = AdminLoginRequest(
            email=test_admin_user.email,
            password="wrongpassword"
        )

        authenticated_admin = admin_service.authenticate_admin(login_data)

        assert authenticated_admin is None

    def test_authenticate_admin_nonexistent_user(self, admin_service: AdminService):
        """Test admin authentication with nonexistent user."""
        from app.models.admin import AdminLoginRequest

        login_data = AdminLoginRequest(
            email="nonexistent@test.com",
            password="password123"
        )

        authenticated_admin = admin_service.authenticate_admin(login_data)

        assert authenticated_admin is None

    def test_authenticate_inactive_admin(self, admin_service: AdminService, test_admin_user, db_session):
        """Test authentication with inactive admin user."""
        from app.models.admin import AdminLoginRequest

        # Deactivate admin user
        test_admin_user.is_active = False
        db_session.commit()

        login_data = AdminLoginRequest(
            email=test_admin_user.email,
            password="testpassword123"
        )

        authenticated_admin = admin_service.authenticate_admin(login_data)

        assert authenticated_admin is None

    def test_create_admin_session(self, admin_service: AdminService, test_admin_user):
        """Test creating admin session."""
        session = admin_service.create_admin_session(
            admin_user=test_admin_user,
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )

        assert session.admin_user_id == test_admin_user.id
        assert session.session_token is not None
        assert session.is_active is True
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "Test Agent"
        assert session.expires_at > datetime.utcnow()

    def test_get_admin_permissions(self, admin_service: AdminService, test_admin_user):
        """Test getting admin permissions."""
        permissions = admin_service.get_admin_permissions(test_admin_user)

        # Should return list of permission strings
        assert isinstance(permissions, list)
        # Permissions format should be "resource:action"
        for perm in permissions:
            assert ":" in perm

    def test_has_permission_super_admin(self, admin_service: AdminService, test_super_admin_user):
        """Test that super admin has all permissions."""
        # Super admin should have any permission
        assert admin_service.has_permission(
            test_super_admin_user, "any_resource", "any_action") is True

    def test_logout_admin(self, admin_service: AdminService, test_admin_user):
        """Test admin logout."""
        # Create session first
        session = admin_service.create_admin_session(test_admin_user)

        # Logout
        success = admin_service.logout_admin(test_admin_user.id)

        assert success is True

        # Verify session is deactivated
        updated_session = admin_service.db.query(admin_service.db.query(
            type(session)).filter_by(id=session.id)).first()
        if updated_session:
            assert updated_session.is_active is False


class TestAdminEndpoints:
    """Test admin API endpoints."""

    def test_admin_login_success(self, client: TestClient, test_admin_user):
        """Test successful admin login endpoint."""
        response = client.post(
            "/api/v1/admin/login",
            json={
                "email": test_admin_user.email,
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "admin_user" in data
        assert "permissions" in data
        assert data["admin_user"]["email"] == test_admin_user.email

    def test_admin_login_invalid_credentials(self, client: TestClient, test_admin_user):
        """Test admin login with invalid credentials."""
        response = client.post(
            "/api/v1/admin/login",
            json={
                "email": test_admin_user.email,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_admin_logout(self, client: TestClient, test_admin_user):
        """Test admin logout endpoint."""
        # Login first
        login_response = client.post(
            "/api/v1/admin/login",
            json={
                "email": test_admin_user.email,
                "password": "testpassword123"
            }
        )

        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/v1/admin/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

    def test_get_admin_profile(self, client: TestClient, test_admin_user):
        """Test getting admin profile."""
        # Login first
        login_response = client.post(
            "/api/v1/admin/login",
            json={
                "email": test_admin_user.email,
                "password": "testpassword123"
            }
        )

        token = login_response.json()["access_token"]

        # Get profile
        response = client.get(
            "/api/v1/admin/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == test_admin_user.email
        assert data["name"] == test_admin_user.name
        assert data["role"] == test_admin_user.role
        assert data["is_active"] is True

    def test_create_admin_user_endpoint(self, client: TestClient, test_super_admin_user):
        """Test creating admin user via endpoint."""
        # Login as super admin first
        login_response = client.post(
            "/api/v1/admin/login",
            json={
                "email": test_super_admin_user.email,
                "password": "superpassword123"
            }
        )

        token = login_response.json()["access_token"]

        # Create new admin user
        response = client.post(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "newadmin@test.com",
                "name": "New Admin",
                "password": "newpassword123",
                "role": "admin"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == "newadmin@test.com"
        assert data["name"] == "New Admin"
        assert data["role"] == "admin"
        assert data["is_active"] is True

    def test_unauthorized_access(self, client: TestClient):
        """Test accessing admin endpoints without authentication."""
        response = client.get("/api/v1/admin/me")

        assert response.status_code == 401

    def test_insufficient_permissions(self, client: TestClient, test_admin_user):
        """Test accessing super admin endpoints with regular admin."""
        # Login as regular admin
        login_response = client.post(
            "/api/v1/admin/login",
            json={
                "email": test_admin_user.email,
                "password": "testpassword123"
            }
        )

        token = login_response.json()["access_token"]

        # Try to create admin user (requires super admin)
        response = client.post(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "newadmin@test.com",
                "name": "New Admin",
                "password": "newpassword123",
                "role": "admin"
            }
        )

        assert response.status_code == 403
        assert "Super admin access required" in response.json()["detail"]
