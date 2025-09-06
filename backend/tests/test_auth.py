"""Tests for authentication functionality."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token, verify_token, verify_password,
    get_password_hash, create_authentication_exception
)
from app.models.user import Student, StudentCreate, LoginRequest
from app.services.user_service import UserService


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_and_verify_token(self):
        """Test token creation and verification."""
        user_id = str(uuid4())
        token = create_access_token(subject=user_id)

        assert token is not None
        assert isinstance(token, str)

        verified_id = verify_token(token)
        assert verified_id == user_id

    def test_token_with_custom_expiry(self):
        """Test token creation with custom expiry."""
        user_id = str(uuid4())
        expires_delta = timedelta(minutes=30)
        token = create_access_token(
            subject=user_id, expires_delta=expires_delta)

        verified_id = verify_token(token)
        assert verified_id == user_id

    def test_invalid_token_verification(self):
        """Test verification of invalid tokens."""
        assert verify_token("invalid_token") is None
        assert verify_token("") is None
        assert verify_token(
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid") is None

    def test_authentication_exception(self):
        """Test authentication exception creation."""
        exception = create_authentication_exception()
        assert exception.status_code == 401
        assert "Could not validate credentials" in exception.detail


class TestUserService:
    """Test user service operations."""

    def test_create_user_success(self, db_session: Session):
        """Test successful user creation."""
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="test@example.com",
            name="Test User",
            password="password123"
        )

        user = user_service.create_user(user_data)

        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.password_hash != "password123"  # Should be hashed
        assert user.history_enabled is False  # Default value
        assert user.id is not None

    def test_create_user_duplicate_email(self, db_session: Session):
        """Test user creation with duplicate email."""
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="duplicate@example.com",
            name="User One",
            password="password123"
        )

        # Create first user
        user_service.create_user(user_data)

        # Try to create second user with same email
        user_data2 = StudentCreate(
            email="duplicate@example.com",
            name="User Two",
            password="password456"
        )

        with pytest.raises(Exception):  # Should raise HTTPException
            user_service.create_user(user_data2)

    def test_authenticate_user_success(self, db_session: Session):
        """Test successful user authentication."""
        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="auth@example.com",
            name="Auth User",
            password="password123"
        )
        created_user = user_service.create_user(user_data)

        # Authenticate user
        login_data = LoginRequest(
            email="auth@example.com",
            password="password123"
        )
        authenticated_user = user_service.authenticate_user(login_data)

        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.email == "auth@example.com"

    def test_authenticate_user_wrong_password(self, db_session: Session):
        """Test authentication with wrong password."""
        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="wrongpass@example.com",
            name="Wrong Pass User",
            password="password123"
        )
        user_service.create_user(user_data)

        # Try to authenticate with wrong password
        login_data = LoginRequest(
            email="wrongpass@example.com",
            password="wrongpassword"
        )
        authenticated_user = user_service.authenticate_user(login_data)

        assert authenticated_user is None

    def test_authenticate_user_nonexistent_email(self, db_session: Session):
        """Test authentication with non-existent email."""
        user_service = UserService(db_session)

        login_data = LoginRequest(
            email="nonexistent@example.com",
            password="password123"
        )
        authenticated_user = user_service.authenticate_user(login_data)

        assert authenticated_user is None

    def test_create_login_response(self, db_session: Session):
        """Test login response creation."""
        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="loginresp@example.com",
            name="Login Response User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        # Create login response
        login_response = user_service.create_login_response(user)

        assert login_response.access_token is not None
        assert login_response.token_type == "bearer"
        assert login_response.expires_in > 0
        assert login_response.student.email == "loginresp@example.com"
        assert login_response.student.name == "Login Response User"

    def test_get_user_by_id(self, db_session: Session):
        """Test getting user by ID."""
        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="getbyid@example.com",
            name="Get By ID User",
            password="password123"
        )
        created_user = user_service.create_user(user_data)

        # Get user by ID
        retrieved_user = user_service.get_user_by_id(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "getbyid@example.com"

    def test_get_user_by_email(self, db_session: Session):
        """Test getting user by email."""
        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="getbyemail@example.com",
            name="Get By Email User",
            password="password123"
        )
        created_user = user_service.create_user(user_data)

        # Get user by email
        retrieved_user = user_service.get_user_by_email(
            "getbyemail@example.com")

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "getbyemail@example.com"

    def test_update_user(self, db_session: Session):
        """Test user profile update."""
        from app.models.user import StudentUpdate

        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="update@example.com",
            name="Original Name",
            password="password123"
        )
        created_user = user_service.create_user(user_data)

        # Update user
        update_data = StudentUpdate(
            name="Updated Name",
            history_enabled=True
        )
        updated_user = user_service.update_user(created_user.id, update_data)

        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.history_enabled is True
        assert updated_user.email == "update@example.com"  # Should remain unchanged

    def test_delete_user(self, db_session: Session):
        """Test user deletion."""
        user_service = UserService(db_session)

        # Create user
        user_data = StudentCreate(
            email="delete@example.com",
            name="Delete User",
            password="password123"
        )
        created_user = user_service.create_user(user_data)
        user_id = created_user.id

        # Delete user
        success = user_service.delete_user(user_id)
        assert success is True

        # Verify user is deleted
        deleted_user = user_service.get_user_by_id(user_id)
        assert deleted_user is None


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    def test_register_endpoint(self, client: TestClient, db_session: Session):
        """Test user registration endpoint."""
        user_data = {
            "email": "register@example.com",
            "name": "Register User",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "register@example.com"
        assert data["name"] == "Register User"
        assert "id" in data
        assert data["history_enabled"] is False

    def test_register_duplicate_email(self, client: TestClient, db_session: Session):
        """Test registration with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "name": "First User",
            "password": "password123"
        }

        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201

        # Second registration with same email
        user_data["name"] = "Second User"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    def test_login_endpoint(self, client: TestClient, db_session: Session):
        """Test user login endpoint."""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "name": "Login User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Then login
        login_data = {
            "email": "login@example.com",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["student"]["email"] == "login@example.com"

    def test_login_wrong_credentials(self, client: TestClient, db_session: Session):
        """Test login with wrong credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_current_user_profile(self, client: TestClient, db_session: Session):
        """Test getting current user profile."""
        # Register and login
        user_data = {
            "email": "profile@example.com",
            "name": "Profile User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "profile@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]

        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["name"] == "Profile User"

    def test_update_user_profile(self, client: TestClient, db_session: Session):
        """Test updating user profile."""
        # Register and login
        user_data = {
            "email": "updateprofile@example.com",
            "name": "Original Name",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "updateprofile@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]

        # Update profile
        update_data = {
            "name": "Updated Name",
            "history_enabled": True
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            "/api/v1/auth/me", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["history_enabled"] is True

    def test_unauthorized_access(self, client: TestClient):
        """Test accessing protected endpoints without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

        response = client.put("/api/v1/auth/me", json={"name": "New Name"})
        assert response.status_code == 401

        response = client.delete("/api/v1/auth/me")
        assert response.status_code == 401
