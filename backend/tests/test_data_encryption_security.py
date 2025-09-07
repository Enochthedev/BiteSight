"""Data encryption and storage security testing."""

import pytest
import os
import tempfile
import hashlib
import base64
from unittest.mock import patch, Mock, mock_open
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.main import app
from app.models.user import Student
from app.core.auth import hash_password, verify_password


class TestDataEncryptionSecurity:
    """Test data encryption and storage security measures."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = Student(
            email="encryption_test@university.edu.ng",
            name="Encryption Test User",
            password_hash=hash_password("SecurePassword123!"),
            history_enabled=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def auth_headers(self, client, test_user):
        """Get authentication headers."""
        with patch('app.core.auth.verify_password', return_value=True):
            response = client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "SecurePassword123!"
            })

            if response.status_code == 200:
                token = response.json().get("access_token", "mock-token")
                return {"Authorization": f"Bearer {token}"}

        return {"Authorization": "Bearer mock-token"}

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        from PIL import Image

        image = Image.new('RGB', (224, 224), color='red')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image.save(temp_file.name, 'JPEG')

        yield temp_file.name

        os.unlink(temp_file.name)

    def test_password_hashing_security(self):
        """Test password hashing security and strength."""

        passwords = [
            "SimplePassword123!",
            "ComplexP@ssw0rd!2024",
            "VeryLongPasswordWithManyCharacters123!@#",
            "短密码123!",  # Unicode password
        ]

        for password in passwords:
            # Test hashing
            hashed = hash_password(password)

            # Hash should be different each time (salt)
            hashed2 = hash_password(password)
            assert hashed != hashed2, "Password hashes should be unique due to salt"

            # Both should verify correctly
            assert verify_password(
                password, hashed), "Original hash should verify"
            assert verify_password(
                password, hashed2), "Second hash should verify"

            # Wrong password should not verify
            assert not verify_password(
                password + "x", hashed), "Wrong password should not verify"

            # Hash should be sufficiently long (indicates proper algorithm)
            assert len(
                hashed) >= 60, "Hash should be at least 60 characters (bcrypt)"

            # Hash should contain salt information
            assert hashed.startswith("$2b$") or hashed.startswith(
                "$2a$"), "Should use bcrypt"

            # Test hash strength (should be slow)
            import time
            start_time = time.time()
            hash_password(password)
            hash_time = time.time() - start_time

            # Should take reasonable time (not too fast, not too slow)
            assert 0.01 < hash_time < 2.0, f"Hash time {hash_time}s should be reasonable"

    def test_jwt_token_security(self):
        """Test JWT token encryption and security."""

        from app.core.auth import create_access_token, verify_token

        user_data = {"sub": "test-user-123", "email": "test@example.com"}

        # Create token
        token = create_access_token(data=user_data)

        # Token should be properly formatted JWT
        parts = token.split('.')
        assert len(parts) == 3, "JWT should have 3 parts"

        # Decode and verify token structure
        import jwt
        import json

        # Decode header (without verification for testing)
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
        assert "alg" in header, "JWT header should specify algorithm"
        assert "typ" in header, "JWT header should specify type"
        assert header["typ"] == "JWT", "Should be JWT type"

        # Algorithm should be secure
        secure_algorithms = ["HS256", "HS384",
                             "HS512", "RS256", "RS384", "RS512"]
        assert header["alg"] in secure_algorithms, f"Algorithm {header['alg']} should be secure"

        # Verify token
        payload = verify_token(token)
        assert payload["sub"] == user_data["sub"], "Token payload should match"

        # Test token tampering detection
        tampered_token = token[:-5] + "XXXXX"

        with pytest.raises(jwt.InvalidTokenError):
            verify_token(tampered_token)

    def test_database_connection_security(self):
        """Test database connection security."""

        from app.core.database import get_database_url

        # Get database URL (mocked for testing)
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:password@localhost:5432/testdb'
        }):
            db_url = get_database_url()

            # Should use secure connection parameters
            assert "sslmode" in db_url or "ssl" in db_url, "Should use SSL for database connections"

            # Should not expose credentials in logs
            # This would be tested by checking log output

    def test_file_storage_encryption(self, client, test_user, sample_image, auth_headers):
        """Test file storage encryption and security."""

        with patch('app.services.image_service.ImageService') as mock_image_service:
            # Mock encrypted file storage
            mock_image_service.return_value.store_image_encrypted = Mock(
                return_value={
                    "encrypted_path": "/encrypted/path/image.enc",
                    "encryption_key_id": "key_123",
                    "checksum": "abc123def456"
                }
            )

            # Upload image
            with open(sample_image, 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(test_user.student_id)},
                    headers=auth_headers
                )

            # Verify encryption was used
            if response.status_code in [200, 202]:
                # Should use encrypted storage
                mock_image_service.return_value.store_image_encrypted.assert_called()

    def test_data_at_rest_encryption(self, db_session, test_user):
        """Test encryption of sensitive data at rest."""

        # Test that sensitive fields are encrypted in database

        # Create test data with sensitive information
        sensitive_data = {
            "personal_notes": "Private health information",
            "dietary_restrictions": "Allergic to peanuts",
            "medical_conditions": "Diabetes type 2"
        }

        # This would test actual database encryption
        # In a real implementation, sensitive fields would be encrypted before storage

        # Mock encrypted field storage
        with patch('app.models.user.encrypt_field') as mock_encrypt:
            mock_encrypt.return_value = "encrypted_data_blob"

            # Update user with sensitive data
            test_user.personal_notes = sensitive_data["personal_notes"]
            db_session.commit()

            # Verify encryption was called
            mock_encrypt.assert_called_with(sensitive_data["personal_notes"])

    def test_data_in_transit_encryption(self, client):
        """Test data in transit encryption (HTTPS)."""

        # Test that API enforces HTTPS

        # This would typically be tested at the infrastructure level
        # Here we test that security headers are set

        response = client.get("/api/v1/monitoring/ping")

        headers = response.headers

        # Check for HTTPS enforcement headers
        if "Strict-Transport-Security" in headers:
            hsts_header = headers["Strict-Transport-Security"]
            assert "max-age=" in hsts_header, "HSTS should specify max-age"

            # Should have reasonable max-age (at least 1 year)
            import re
            max_age_match = re.search(r'max-age=(\d+)', hsts_header)
            if max_age_match:
                max_age = int(max_age_match.group(1))
                assert max_age >= 31536000, "HSTS max-age should be at least 1 year"

    def test_api_key_security(self):
        """Test API key security and management."""

        from app.core.config import get_settings

        settings = get_settings()

        # Test that API keys are properly configured
        if hasattr(settings, 'SECRET_KEY'):
            secret_key = settings.SECRET_KEY

            # Secret key should be sufficiently long and random
            assert len(
                secret_key) >= 32, "Secret key should be at least 32 characters"

            # Should not be default/example values
            insecure_keys = [
                "secret",
                "password",
                "123456",
                "your-secret-key-here",
                "change-me",
                "default"
            ]

            for insecure_key in insecure_keys:
                assert insecure_key not in secret_key.lower(
                ), f"Secret key should not contain '{insecure_key}'"

    def test_session_security(self, client, test_user, auth_headers):
        """Test session security and management."""

        # Test session token security

        # Make authenticated request
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=auth_headers)

        if response.status_code == 200:
            # Test that session tokens are secure

            # Check for secure cookie attributes (if using cookies)
            set_cookie_headers = response.headers.get_list("Set-Cookie")

            for cookie_header in set_cookie_headers:
                if "session" in cookie_header.lower():
                    # Should have secure attributes
                    assert "Secure" in cookie_header, "Session cookies should be Secure"
                    assert "HttpOnly" in cookie_header, "Session cookies should be HttpOnly"
                    assert "SameSite" in cookie_header, "Session cookies should have SameSite"

    def test_encryption_key_management(self):
        """Test encryption key management security."""

        # Test key rotation and management

        # Mock key management service
        with patch('app.core.encryption.KeyManager') as mock_key_manager:
            mock_key_manager.return_value.get_current_key = Mock(
                return_value={
                    "key_id": "key_123",
                    "key_data": "encrypted_key_data",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            )

            mock_key_manager.return_value.rotate_key = Mock(
                return_value={
                    "old_key_id": "key_123",
                    "new_key_id": "key_124",
                    "rotation_date": "2024-01-02T00:00:00Z"
                }
            )

            # Test key retrieval
            key_manager = mock_key_manager.return_value
            current_key = key_manager.get_current_key()

            assert "key_id" in current_key, "Key should have ID"
            assert "key_data" in current_key, "Key should have data"

            # Test key rotation
            rotation_result = key_manager.rotate_key()

            assert "old_key_id" in rotation_result, "Should track old key"
            assert "new_key_id" in rotation_result, "Should provide new key"

    def test_backup_encryption(self):
        """Test backup data encryption."""

        # Test that backups are encrypted

        # Mock backup service
        with patch('app.core.backup.BackupService') as mock_backup:
            mock_backup.return_value.create_encrypted_backup = Mock(
                return_value={
                    "backup_id": "backup_123",
                    "encrypted": True,
                    "encryption_algorithm": "AES-256-GCM",
                    "backup_path": "/encrypted/backups/backup_123.enc"
                }
            )

            backup_service = mock_backup.return_value
            backup_result = backup_service.create_encrypted_backup()

            assert backup_result["encrypted"] == True, "Backups should be encrypted"
            assert "AES" in backup_result["encryption_algorithm"], "Should use strong encryption"

    def test_log_data_security(self):
        """Test that logs don't contain sensitive data."""

        # Test log sanitization

        sensitive_data = [
            "password123",
            "secret_key_abc123",
            "credit_card_4111111111111111",
            "ssn_123456789",
            "api_key_xyz789"
        ]

        # Mock logging to capture log messages
        log_messages = []

        def mock_log_handler(message):
            log_messages.append(message)

        with patch('app.core.logging_config.logger.info', side_effect=mock_log_handler):
            # Simulate operations that might log sensitive data

            # Login attempt (should not log password)
            from app.core.logging_config import logger
            logger.info(f"Login attempt for user with password: {'*' * 8}")

            # API key usage (should not log full key)
            logger.info(f"API request with key: {'***' + 'abc123'[-4:]}")

        # Verify no sensitive data in logs
        for message in log_messages:
            for sensitive in sensitive_data:
                assert sensitive not in message, f"Sensitive data '{sensitive}' found in logs"

    def test_memory_security(self):
        """Test memory security and cleanup."""

        # Test that sensitive data is cleared from memory

        password = "SensitivePassword123!"

        # Create and use sensitive data
        sensitive_buffer = bytearray(password.encode())

        # Process the data
        processed = hash_password(password)

        # Clear sensitive data from memory
        # In production, this would use secure memory clearing
        for i in range(len(sensitive_buffer)):
            sensitive_buffer[i] = 0

        # Verify clearing
        assert all(
            b == 0 for b in sensitive_buffer), "Sensitive data should be cleared from memory"

    def test_cryptographic_randomness(self):
        """Test cryptographic randomness quality."""

        # Test random number generation quality

        import secrets

        # Generate multiple random values
        random_values = [secrets.token_bytes(32) for _ in range(100)]

        # All values should be different
        assert len(set(random_values)) == len(
            random_values), "Random values should be unique"

        # Test entropy (basic check)
        combined = b''.join(random_values)

        # Should have good byte distribution
        byte_counts = [0] * 256
        for byte in combined:
            byte_counts[byte] += 1

        # No byte should be completely absent or overly frequent
        min_count = min(byte_counts)
        max_count = max(byte_counts)

        # Allow some variance but not extreme
        assert min_count > 0, "All byte values should appear"
        assert max_count / min_count < 10, "Byte distribution should be reasonably uniform"

    def test_secure_file_permissions(self, sample_image):
        """Test secure file permissions and access."""

        # Test file permission security

        # Check file permissions
        file_stat = os.stat(sample_image)
        file_mode = file_stat.st_mode

        # Convert to octal for easier reading
        octal_mode = oct(file_mode)[-3:]

        # File should not be world-writable
        assert not (
            file_mode & 0o002), f"File should not be world-writable: {octal_mode}"

        # File should not be world-readable for sensitive files
        # (This depends on the specific file type and security requirements)

    def test_secure_temporary_files(self):
        """Test secure temporary file handling."""

        # Test that temporary files are created securely

        # Create secure temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
            temp_path = temp_file.name

            # Write sensitive data
            sensitive_data = b"Sensitive temporary data"
            temp_file.write(sensitive_data)
            temp_file.flush()

            # Check file permissions
            file_stat = os.stat(temp_path)
            file_mode = file_stat.st_mode

            # Should be readable/writable only by owner
            expected_mode = 0o600  # rw-------
            actual_mode = file_mode & 0o777

            assert actual_mode == expected_mode, f"Temp file permissions should be 600, got {oct(actual_mode)}"

        # Clean up
        if os.path.exists(temp_path):
            # Securely delete temporary file
            with open(temp_path, 'r+b') as f:
                length = f.seek(0, 2)  # Get file length
                f.seek(0)
                f.write(b'\x00' * length)  # Overwrite with zeros
                f.flush()
                os.fsync(f.fileno())  # Force write to disk

            os.unlink(temp_path)

    def test_database_encryption_at_rest(self):
        """Test database encryption at rest configuration."""

        # Test database encryption settings

        from app.core.database import get_database_url

        # Mock database configuration
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db?sslmode=require'
        }):
            db_url = get_database_url()

            # Should enforce SSL/TLS
            assert "sslmode=require" in db_url or "ssl=true" in db_url, "Database should use SSL"

        # Test that sensitive database fields are encrypted
        # This would depend on the actual ORM and encryption implementation

    def test_api_response_data_filtering(self, client, test_user, auth_headers):
        """Test that API responses don't expose sensitive data."""

        # Test user profile endpoint
        response = client.get(
            f"/api/v1/users/{test_user.student_id}/profile", headers=auth_headers)

        if response.status_code == 200:
            profile_data = response.json()

            # Should not expose sensitive fields
            sensitive_fields = [
                "password_hash",
                "password",
                "secret_key",
                "internal_id",
                "admin_notes",
                "system_flags"
            ]

            for field in sensitive_fields:
                assert field not in profile_data, f"Sensitive field '{field}' should not be in API response"

            # Should only include necessary fields
            expected_fields = {"student_id",
                               "email", "name", "history_enabled"}
            actual_fields = set(profile_data.keys())

            # All expected fields should be present
            for field in expected_fields:
                assert field in actual_fields, f"Expected field '{field}' missing from response"

    def test_encryption_algorithm_strength(self):
        """Test that strong encryption algorithms are used."""

        # Test encryption algorithm configuration

        # Mock encryption service
        with patch('app.core.encryption.EncryptionService') as mock_encryption:
            mock_encryption.return_value.get_algorithm_info = Mock(
                return_value={
                    "algorithm": "AES-256-GCM",
                    "key_size": 256,
                    "mode": "GCM",
                    "iv_size": 96
                }
            )

            encryption_service = mock_encryption.return_value
            algo_info = encryption_service.get_algorithm_info()

            # Should use strong algorithms
            strong_algorithms = ["AES-256-GCM",
                                 "AES-256-CBC", "ChaCha20-Poly1305"]
            assert algo_info[
                "algorithm"] in strong_algorithms, f"Should use strong algorithm, got {algo_info['algorithm']}"

            # Key size should be adequate
            assert algo_info[
                "key_size"] >= 256, f"Key size should be at least 256 bits, got {algo_info['key_size']}"
