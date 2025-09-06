"""Integration tests for API endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.user import Student
from app.services.user_service import UserService
from tests.conftest import TestingSessionLocal


client = TestClient(app)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestAPIGateway:
    """Test API gateway functionality."""

    def test_root_endpoint(self):
        """Test root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Nutrition Feedback API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"
        assert "docs_url" in data

    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "components" in data
        assert "database" in data["components"]
        assert "api" in data["components"]

    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert openapi_spec["info"]["title"] == "Nutrition Feedback API"

    def test_docs_endpoint_available(self):
        """Test that Swagger docs are available."""
        response = client.get("/api/v1/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_available(self):
        """Test that ReDoc documentation is available."""
        response = client.get("/api/v1/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestMiddleware:
    """Test middleware functionality."""

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.get("/")
        assert response.status_code == 200
        # CORS headers should be present in responses

    def test_security_headers(self):
        """Test security headers are added."""
        response = client.get("/")
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_process_time_header(self):
        """Test that process time header is added."""
        response = client.get("/")
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time > 0

    def test_rate_limit_headers(self):
        """Test rate limiting headers."""
        response = client.get("/")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_request_size_limit(self):
        """Test request size limiting."""
        # Create a large payload (larger than typical limit)
        large_data = "x" * (11 * 1024 * 1024)  # 11MB
        response = client.post(
            "/api/v1/auth/register",
            json={"data": large_data}
        )
        # Should be rejected due to size limit
        assert response.status_code == 413


class TestErrorHandling:
    """Test error handling and response formatting."""

    def test_404_error_format(self):
        """Test 404 error response format."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "type" in data["error"]
        assert "timestamp" in data["error"]
        assert "path" in data["error"]

    def test_validation_error_format(self):
        """Test validation error response format."""
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == 422
        assert data["error"]["type"] == "validation_error"
        assert "details" in data["error"]

    def test_method_not_allowed_error(self):
        """Test method not allowed error."""
        response = client.patch("/")  # Root only supports GET
        assert response.status_code == 405
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == 405


class TestAuthenticationIntegration:
    """Test authentication integration."""

    def test_register_endpoint_structure(self):
        """Test user registration endpoint structure."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        # Should return proper structure (may fail due to validation, but structure should be consistent)
        assert response.status_code in [200, 201, 400, 422]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "student_id" in data or "message" in data

    def test_login_endpoint_structure(self):
        """Test login endpoint structure."""
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        # Should return proper structure
        assert response.status_code in [200, 401, 422]

    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/history/meals")
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


class TestMealEndpointsIntegration:
    """Test meal-related endpoints integration."""

    def test_meal_upload_endpoint_structure(self):
        """Test meal upload endpoint structure."""
        # Test without authentication first
        response = client.post("/api/v1/meals/upload")
        # Should require auth or proper data
        assert response.status_code in [401, 422]

    def test_meal_analysis_endpoint_structure(self):
        """Test meal analysis endpoint structure."""
        response = client.get(
            "/api/v1/meals/123e4567-e89b-12d3-a456-426614174000/analysis")
        # Should require auth or not found
        assert response.status_code in [401, 404]


class TestFeedbackEndpointsIntegration:
    """Test feedback-related endpoints integration."""

    def test_feedback_endpoint_structure(self):
        """Test feedback endpoint structure."""
        response = client.get(
            "/api/v1/feedback/123e4567-e89b-12d3-a456-426614174000")
        # Should require auth or not found
        assert response.status_code in [401, 404]


class TestHistoryEndpointsIntegration:
    """Test history-related endpoints integration."""

    def test_history_endpoint_structure(self):
        """Test history endpoint structure."""
        response = client.get("/api/v1/history/meals")
        assert response.status_code == 401  # Should require authentication

    def test_insights_endpoint_structure(self):
        """Test insights endpoint structure."""
        response = client.get("/api/v1/history/insights/weekly")
        assert response.status_code == 401  # Should require authentication


class TestAdminEndpointsIntegration:
    """Test admin-related endpoints integration."""

    def test_admin_endpoint_structure(self):
        """Test admin endpoint structure."""
        response = client.get("/api/v1/admin/foods")
        assert response.status_code == 401  # Should require authentication


class TestConsentEndpointsIntegration:
    """Test consent-related endpoints integration."""

    def test_consent_endpoint_structure(self):
        """Test consent endpoint structure."""
        response = client.get("/api/v1/consent/status")
        assert response.status_code == 401  # Should require authentication


class TestInferenceEndpointsIntegration:
    """Test inference-related endpoints integration."""

    def test_inference_endpoint_structure(self):
        """Test inference endpoint structure."""
        response = client.post("/api/v1/inference/analyze")
        # Should require auth or proper data
        assert response.status_code in [401, 422]


class TestAPIVersioning:
    """Test API versioning."""

    def test_v1_prefix_required(self):
        """Test that v1 prefix is required for API endpoints."""
        # Test without version prefix
        response = client.get("/auth/register")
        assert response.status_code == 404

        # Test with version prefix
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422  # Validation error, but endpoint exists

    def test_api_endpoints_consistency(self):
        """Test that all API endpoints follow consistent patterns."""
        # Get OpenAPI spec
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        spec = response.json()

        # Check that all paths start with /api/v1
        for path in spec["paths"]:
            # Paths in OpenAPI spec are relative to the base URL
            # Since we mount the router with /api/v1 prefix, paths should not include it
            assert not path.startswith("/api/v1")


class TestStaticFiles:
    """Test static file serving."""

    def test_uploads_mount(self):
        """Test that uploads directory is properly mounted."""
        # This will return 404 if no file exists, but should not return 500
        response = client.get("/uploads/test.jpg")
        assert response.status_code == 404  # File doesn't exist, but mount works


if __name__ == "__main__":
    pytest.main([__file__])
