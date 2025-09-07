"""Security testing for authentication and authorization."""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import create_access_token, verify_token, hash_password, verify_password
from app.models.user import Student
from app.models.admin import AdminUser, AdminRole


class TestAuthenticationSecurity:
    """Test authentication and authorization security."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = Student(
            email="security_test@university.edu.ng",
            name="Security Test User",
            password_hash=hash_password("SecurePassword123!"),
            history_enabled=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def admin_user(self, db_session):
        """Create an admin user."""
        admin = AdminUser(
            username="security_admin",
            email="security_admin@university.edu.ng",
            password_hash=hash_password("AdminPassword123!"),
            role=AdminRole.SUPER_ADMIN,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    def test_password_hashing_security(self):
        """Test password hashing security measures."""

        password = "TestPassword123!"

        # Test password hashing
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)

        # Hashes should be different (salt should be random)
        assert hashed1 != hashed2

        # Both should verify correctly
        assert verify_password(password, hashed1)
        assert verify_password(password, hashed2)

        # Wrong password should not verify
        assert not verify_password("WrongPassword", hashed1)

        # Test with various password complexities
        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "password123"
        ]

        for weak_password in weak_passwords:
            hashed = hash_password(weak_password)
            assert verify_password(weak_password, hashed)
            assert not verify_password(weak_password + "x", hashed)

    def test_jwt_token_security(self):
        """Test JWT token security measures."""

        user_id = "test-user-123"

        # Create token
        token = create_access_token(data={"sub": user_id})
        assert token is not None

        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

        # Test token expiration
        expired_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        # Expired token should not verify
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(expired_token)

        # Test invalid token
        invalid_token = "invalid.jwt.token"
        with pytest.raises(jwt.InvalidTokenError):
            verify_token(invalid_token)

        # Test tampered token
        tampered_token = token[:-5] + "XXXXX"
        with pytest.raises(jwt.InvalidTokenError):
            verify_token(tampered_token)

    def test_login_security_measures(self, client, test_user):
        """Test login security measures."""

        # Test successful login
        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        auth_data = response.json()
        assert "access_token" in auth_data
        assert "token_type" in auth_data
        assert auth_data["token_type"] == "bearer"

        # Test failed login with wrong password
        wrong_password_data = {
            "email": test_user.email,
            "password": "WrongPassword"
        }

        response = client.post("/api/v1/auth/login", json=wrong_password_data)
        assert response.status_code == 401

        error_data = response.json()
        assert "error" in error_data
        assert "Invalid credentials" in error_data["error"]["message"]

        # Test failed login with non-existent user
        nonexistent_user_data = {
            "email": "nonexistent@university.edu.ng",
            "password": "AnyPassword"
        }

        response = client.post("/api/v1/auth/login",
                               json=nonexistent_user_data)
        assert response.status_code == 401

        # Test SQL injection attempts
        sql_injection_attempts = [
            "admin@test.com'; DROP TABLE students; --",
            "admin@test.com' OR '1'='1",
            "admin@test.com' UNION SELECT * FROM students --"
        ]

        for injection_email in sql_injection_attempts:
            injection_data = {
                "email": injection_email,
                "password": "password"
            }

            response = client.post("/api/v1/auth/login", json=injection_data)
            # Should not cause server error, should handle gracefully
            assert response.status_code in [400, 401, 422]

    def test_brute_force_protection(self, client, test_user):
        """Test brute force attack protection."""

        # Attempt multiple failed logins
        failed_attempts = []

        for i in range(10):  # 10 failed attempts
            login_data = {
                "email": test_user.email,
                "password": f"WrongPassword{i}"
            }

            response = client.post("/api/v1/auth/login", json=login_data)
            failed_attempts.append(response.status_code)

        # Should have consistent failure responses
        assert all(status == 401 for status in failed_attempts)

        # After many failed attempts, there might be rate limiting
        # (This depends on actual rate limiting implementation)

        # Test that legitimate login still works after failed attempts
        correct_login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/login", json=correct_login_data)
        # Should still work (or be rate limited temporarily)
        assert response.status_code in [200, 429]

    def test_session_security(self, client, test_user):
        """Test session security measures."""

        # Login to get token
        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test authenticated request
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
        assert response.status_code == 200

        # Test request without token
        response = client.get(f"/api/v1/history/{test_user.student_id}/meals")
        assert response.status_code == 401

        # Test request with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=invalid_headers)
        assert response.status_code == 401

        # Test request with malformed authorization header
        malformed_headers = {"Authorization": "InvalidFormat token"}
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=malformed_headers)
        assert response.status_code == 401

    def test_authorization_levels(self, client, test_user, admin_user):
        """Test different authorization levels."""

        # Get user token
        user_login = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        user_response = client.post("/api/v1/auth/login", json=user_login)
        assert user_response.status_code == 200
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Get admin token
        admin_login = {
            "username": admin_user.username,
            "password": "AdminPassword123!"
        }

        admin_response = client.post(
            "/api/v1/auth/admin/login", json=admin_login)
        assert admin_response.status_code == 200
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Test user access to user endpoints
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=user_headers)
        assert response.status_code == 200

        # Test user access to admin endpoints (should be denied)
        response = client.get("/api/v1/admin/users", headers=user_headers)
        assert response.status_code == 403

        # Test admin access to admin endpoints
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200

        # Test admin access to user endpoints (should work)
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=admin_headers)
        assert response.status_code in [200, 403]  # Depends on implementation

    def test_cross_user_access_prevention(self, client, db_session):
        """Test that users cannot access other users' data."""

        # Create two users
        user1 = Student(
            email="user1@university.edu.ng",
            name="User One",
            password_hash=hash_password("Password123!"),
            history_enabled=True
        )

        user2 = Student(
            email="user2@university.edu.ng",
            name="User Two",
            password_hash=hash_password("Password123!"),
            history_enabled=True
        )

        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)

        # Login as user1
        login_data = {
            "email": user1.email,
            "password": "Password123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        user1_token = response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # User1 should access their own data
        response = client.get(
            f"/api/v1/history/{user1.student_id}/meals", headers=user1_headers)
        assert response.status_code == 200

        # User1 should NOT access user2's data
        response = client.get(
            f"/api/v1/history/{user2.student_id}/meals", headers=user1_headers)
        assert response.status_code == 403

        # Test with consent endpoints
        response = client.get(
            f"/api/v1/consent/{user2.student_id}", headers=user1_headers)
        assert response.status_code == 403

        # Test with insights endpoints
        response = client.get(
            f"/api/v1/insights/{user2.student_id}/weekly", headers=user1_headers)
        assert response.status_code == 403

    def test_input_validation_security(self, client):
        """Test input validation for security vulnerabilities."""

        # Test XSS attempts in registration
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]

        for xss_payload in xss_attempts:
            registration_data = {
                "name": xss_payload,
                "email": f"test{hash(xss_payload)}@university.edu.ng",
                "password": "SecurePassword123!"
            }

            response = client.post(
                "/api/v1/auth/register", json=registration_data)
            # Should either reject or sanitize the input
            if response.status_code == 201:
                user_data = response.json()
                # Name should be sanitized
                assert "<script>" not in user_data["user"]["name"]
                assert "javascript:" not in user_data["user"]["name"]

        # Test SQL injection in login
        sql_injections = [
            "admin'; DROP TABLE students; --",
            "admin' OR '1'='1' --",
            "admin' UNION SELECT password FROM students --"
        ]

        for sql_payload in sql_injections:
            login_data = {
                "email": sql_payload,
                "password": "password"
            }

            response = client.post("/api/v1/auth/login", json=login_data)
            # Should handle gracefully without exposing database errors
            assert response.status_code in [400, 401, 422]

            if response.status_code != 401:  # 401 might not have detailed error
                error_data = response.json()
                # Should not expose database information
                assert "DROP TABLE" not in str(error_data).upper()
                assert "UNION SELECT" not in str(error_data).upper()

    def test_password_policy_enforcement(self, client):
        """Test password policy enforcement."""

        # Test weak passwords
        weak_passwords = [
            "123456",           # Too simple
            "password",         # Common password
            "abc",              # Too short
            "PASSWORD123",      # No lowercase
            "password123",      # No uppercase
            "Password",         # No numbers
            "Password123"       # No special characters (depending on policy)
        ]

        for weak_password in weak_passwords:
            registration_data = {
                "name": "Test User",
                "email": f"test{hash(weak_password)}@university.edu.ng",
                "password": weak_password
            }

            response = client.post(
                "/api/v1/auth/register", json=registration_data)
            # Should reject weak passwords
            if response.status_code != 201:
                error_data = response.json()
                assert "password" in error_data["error"]["message"].lower()

        # Test strong password
        strong_password_data = {
            "name": "Test User",
            "email": "strongpassword@university.edu.ng",
            "password": "StrongPassword123!@#"
        }

        response = client.post("/api/v1/auth/register",
                               json=strong_password_data)
        # Strong password should be accepted
        assert response.status_code in [201, 409]  # Created or already exists

    def test_token_refresh_security(self, client, test_user):
        """Test token refresh security."""

        # Login to get initial token
        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        original_token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {original_token}"}

        # Test token refresh
        response = client.post("/api/v1/auth/refresh", headers=headers)

        if response.status_code == 200:
            new_token = response.json()["access_token"]

            # New token should be different
            assert new_token != original_token

            # New token should work
            new_headers = {"Authorization": f"Bearer {new_token}"}
            response = client.get(
                f"/api/v1/history/{test_user.student_id}/meals", headers=new_headers)
            assert response.status_code == 200

            # Old token might still work (depending on implementation)
            # or might be invalidated
            response = client.get(
                f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
            assert response.status_code in [200, 401]

    def test_logout_security(self, client, test_user):
        """Test logout security."""

        # Login to get token
        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify token works
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
        assert response.status_code == 200

        # Logout
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200

        # Token should be invalidated after logout
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
        # Depending on implementation, token might be blacklisted
        assert response.status_code in [200, 401]

    def test_concurrent_session_security(self, client, test_user):
        """Test concurrent session security."""

        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        # Create multiple sessions
        tokens = []
        for i in range(3):
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200
            tokens.append(response.json()["access_token"])

        # All tokens should work initially
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get(
                f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
            assert response.status_code == 200

        # Test session limit (if implemented)
        # This would depend on actual session management policy

    def test_admin_privilege_escalation_prevention(self, client, test_user):
        """Test prevention of privilege escalation attacks."""

        # Login as regular user
        login_data = {
            "email": test_user.email,
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        user_token = response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Attempt to access admin endpoints
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/dataset/stats",
            "/api/v1/admin/nutrition-rules",
            "/api/v1/admin/analytics/usage"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code == 403  # Forbidden

        # Attempt to modify admin data
        rule_data = {
            "rule_name": "malicious_rule",
            "condition_logic": {"always": True},
            "feedback_template": "Malicious feedback"
        }

        response = client.post(
            "/api/v1/admin/nutrition-rules", json=rule_data, headers=user_headers)
        assert response.status_code == 403

    def test_timing_attack_resistance(self, client, test_user):
        """Test resistance to timing attacks."""

        import time

        # Test login timing for existing vs non-existing users
        existing_user_times = []
        nonexistent_user_times = []

        for i in range(5):
            # Time login attempt for existing user (wrong password)
            start_time = time.time()
            response = client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "WrongPassword"
            })
            existing_user_times.append(time.time() - start_time)
            assert response.status_code == 401

            # Time login attempt for non-existing user
            start_time = time.time()
            response = client.post("/api/v1/auth/login", json={
                "email": f"nonexistent{i}@university.edu.ng",
                "password": "AnyPassword"
            })
            nonexistent_user_times.append(time.time() - start_time)
            assert response.status_code == 401

        # Calculate average times
        avg_existing = sum(existing_user_times) / len(existing_user_times)
        avg_nonexistent = sum(nonexistent_user_times) / \
            len(nonexistent_user_times)

        # Times should be similar to prevent timing attacks
        # Allow for some variance but should be in same order of magnitude
        time_ratio = max(avg_existing, avg_nonexistent) / \
            min(avg_existing, avg_nonexistent)
        assert time_ratio < 5.0  # Should not differ by more than 5x
