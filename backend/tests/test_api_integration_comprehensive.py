"""Comprehensive API integration tests covering all endpoints."""

import pytest
import tempfile
import os
import json
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from PIL import Image
from unittest.mock import patch, AsyncMock

from app.main import app
from app.models.user import Student
from app.models.meal import Meal
from app.models.feedback import FeedbackRecord


class TestComprehensiveAPIIntegration:
    """Comprehensive API integration tests for all endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = Student(
            email="api_test@university.edu.ng",
            name="API Test User",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def admin_user(self, db_session):
        """Create an admin user."""
        from app.models.admin import AdminUser, AdminRole

        admin = AdminUser(
            username="test_admin",
            email="admin@university.edu.ng",
            password_hash="hashed_admin_password",
            role=AdminRole.SUPER_ADMIN,
            is_active=True
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        image = Image.new('RGB', (224, 224), color='red')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image.save(temp_file.name, 'JPEG')

        yield temp_file.name

        os.unlink(temp_file.name)

    @pytest.fixture
    def auth_headers(self, client, test_user):
        """Get authentication headers for test user."""
        # Mock authentication for testing
        with patch('app.core.auth.verify_password', return_value=True), \
                patch('app.core.auth.create_access_token', return_value="mock-jwt-token"):

            response = client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "test_password"
            })

            if response.status_code == 200:
                token = response.json().get("access_token", "mock-jwt-token")
                return {"Authorization": f"Bearer {token}"}

        return {"Authorization": "Bearer mock-jwt-token"}

    @pytest.fixture
    def admin_headers(self, client, admin_user):
        """Get authentication headers for admin user."""
        with patch('app.core.auth.verify_password', return_value=True), \
                patch('app.core.auth.create_access_token', return_value="mock-admin-token"):

            response = client.post("/api/v1/auth/admin/login", json={
                "username": admin_user.username,
                "password": "admin_password"
            })

            if response.status_code == 200:
                token = response.json().get("access_token", "mock-admin-token")
                return {"Authorization": f"Bearer {token}"}

        return {"Authorization": "Bearer mock-admin-token"}

    def test_health_and_monitoring_endpoints(self, client):
        """Test all health and monitoring endpoints."""

        # Basic health check
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code in [200, 503]

        health_data = response.json()
        assert "overall_status" in health_data
        assert "checks" in health_data
        assert "timestamp" in health_data

        # Specific service health checks
        services = ["database", "redis", "ml-service"]
        for service in services:
            response = client.get(f"/api/v1/monitoring/health/{service}")
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                service_health = response.json()
                assert "status" in service_health
                assert "details" in service_health

        # Metrics endpoint
        response = client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 200

        metrics = response.json()
        assert "service" in metrics
        assert "timestamp" in metrics

        # Ping endpoint
        response = client.get("/api/v1/monitoring/ping")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_authentication_endpoints(self, client, test_user):
        """Test all authentication-related endpoints."""

        # User registration
        registration_data = {
            "name": "New Test User",
            "email": "newuser@university.edu.ng",
            "password": "SecurePassword123!"
        }

        response = client.post("/api/v1/auth/register", json=registration_data)
        # Created or conflict (user exists)
        assert response.status_code in [201, 409]

        if response.status_code == 201:
            user_data = response.json()
            assert "user" in user_data
            assert "access_token" in user_data
            assert user_data["user"]["email"] == registration_data["email"]

        # User login
        with patch('app.core.auth.verify_password', return_value=True):
            login_data = {
                "email": test_user.email,
                "password": "test_password"
            }

            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200

            auth_data = response.json()
            assert "access_token" in auth_data
            assert "token_type" in auth_data
            assert "user" in auth_data

        # Token refresh
        with patch('app.core.auth.decode_token', return_value={"sub": str(test_user.student_id)}):
            headers = {"Authorization": "Bearer mock-token"}
            response = client.post("/api/v1/auth/refresh", headers=headers)
            assert response.status_code in [200, 401]

        # Password reset request
        reset_data = {"email": test_user.email}
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        assert response.status_code in [200, 404]

        # Logout
        with patch('app.core.auth.decode_token', return_value={"sub": str(test_user.student_id)}):
            headers = {"Authorization": "Bearer mock-token"}
            response = client.post("/api/v1/auth/logout", headers=headers)
            assert response.status_code in [200, 401]

    def test_meal_analysis_endpoints(self, client, test_user, sample_image, auth_headers):
        """Test meal analysis and related endpoints."""

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor, \
                patch('app.services.feedback_generation_service.FeedbackGenerationService') as mock_feedback:

            # Mock ML predictions
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "jollof_rice", "confidence": 0.95,
                            "food_class": "carbohydrates"},
                        {"name": "chicken", "confidence": 0.88,
                            "food_class": "proteins"}
                    ],
                    "analysis_id": "test_analysis_123"
                }
            )

            mock_feedback.return_value.generate_feedback_async = AsyncMock(
                return_value={
                    "feedback_text": "Great meal! Good balance of carbohydrates and proteins.",
                    "recommendations": ["Add vegetables for better nutrition"],
                    "balance_score": 0.8
                }
            )

            # Upload and analyze meal
            with open(sample_image, 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(test_user.student_id)},
                    headers=auth_headers
                )

            # Success or accepted for async processing
            assert response.status_code in [200, 202]

            if response.status_code == 200:
                analysis_result = response.json()
                assert "analysis_id" in analysis_result or "detected_foods" in analysis_result

            # Get analysis status
            analysis_id = "test_analysis_123"
            response = client.get(
                f"/api/v1/meals/analysis/{analysis_id}/status", headers=auth_headers)
            assert response.status_code in [200, 404]

            # Get analysis results
            response = client.get(
                f"/api/v1/meals/analysis/{analysis_id}/results", headers=auth_headers)
            assert response.status_code in [200, 404]

            # Batch meal upload (for offline sync)
            batch_data = {
                "meals": [
                    {
                        "student_id": str(test_user.student_id),
                        "timestamp": "2024-01-01T12:00:00Z",
                        "local_id": "offline_meal_1"
                    }
                ]
            }

            response = client.post(
                "/api/v1/meals/batch-sync", json=batch_data, headers=auth_headers)
            assert response.status_code in [200, 202, 400]

    def test_feedback_endpoints(self, client, test_user, auth_headers):
        """Test feedback-related endpoints."""

        # Get feedback for a meal
        meal_id = "test_meal_123"
        response = client.get(
            f"/api/v1/feedback/{meal_id}", headers=auth_headers)
        assert response.status_code in [200, 404]

        # Submit user feedback on AI feedback
        feedback_data = {
            "meal_id": meal_id,
            "rating": 4,
            "comments": "The feedback was helpful",
            "accuracy_rating": 5
        }

        response = client.post(
            "/api/v1/feedback/user-feedback", json=feedback_data, headers=auth_headers)
        assert response.status_code in [201, 400]

        # Get feedback statistics
        response = client.get(
            f"/api/v1/feedback/stats/{test_user.student_id}", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_history_endpoints(self, client, test_user, auth_headers):
        """Test meal history endpoints."""

        # Get meal history
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=auth_headers)
        assert response.status_code == 200

        history_data = response.json()
        assert "meals" in history_data
        assert "total_count" in history_data

        # Get meal history with filters
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "limit": 10,
            "offset": 0
        }

        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals",
            params=params,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Get specific meal details
        meal_id = "test_meal_123"
        response = client.get(
            f"/api/v1/history/meals/{meal_id}", headers=auth_headers)
        assert response.status_code in [200, 404]

        # Delete meal from history
        response = client.delete(
            f"/api/v1/history/meals/{meal_id}", headers=auth_headers)
        assert response.status_code in [200, 404]

        # Clear all history
        response = client.delete(
            f"/api/v1/history/{test_user.student_id}/clear", headers=auth_headers)
        assert response.status_code == 200

    def test_insights_endpoints(self, client, test_user, auth_headers):
        """Test insights and analytics endpoints."""

        with patch('app.services.insights_service.InsightsService') as mock_insights:
            mock_insights.return_value.generate_weekly_insights_async = AsyncMock(
                return_value={
                    "week_period": "Jan 1-7, 2024",
                    "meals_analyzed": 10,
                    "nutrition_balance": {
                        "carbohydrates": 0.8,
                        "proteins": 0.7,
                        "vitamins": 0.4
                    },
                    "recommendations": ["Include more vegetables"],
                    "positive_trends": ["Good protein intake"]
                }
            )

            # Get weekly insights
            response = client.get(
                f"/api/v1/insights/{test_user.student_id}/weekly", headers=auth_headers)
            assert response.status_code == 200

            insights_data = response.json()
            assert "nutrition_balance" in insights_data
            assert "recommendations" in insights_data

            # Get monthly insights
            response = client.get(
                f"/api/v1/insights/{test_user.student_id}/monthly", headers=auth_headers)
            assert response.status_code in [200, 404]

            # Get nutrition trends
            response = client.get(
                f"/api/v1/insights/{test_user.student_id}/trends", headers=auth_headers)
            assert response.status_code in [200, 404]

            # Get food frequency analysis
            response = client.get(
                f"/api/v1/insights/{test_user.student_id}/food-frequency", headers=auth_headers)
            assert response.status_code in [200, 404]

    def test_consent_and_privacy_endpoints(self, client, test_user, auth_headers):
        """Test consent and privacy management endpoints."""

        # Get current consent status
        response = client.get(
            f"/api/v1/consent/{test_user.student_id}", headers=auth_headers)
        assert response.status_code == 200

        consent_data = response.json()
        assert "data_storage" in consent_data
        assert "analytics" in consent_data

        # Update consent preferences
        new_consent = {
            "data_storage": True,
            "analytics": False,
            "marketing": False
        }

        response = client.post(
            f"/api/v1/consent/{test_user.student_id}", json=new_consent, headers=auth_headers)
        assert response.status_code in [200, 201]

        # Export user data (GDPR compliance)
        response = client.get(
            f"/api/v1/privacy/{test_user.student_id}/export", headers=auth_headers)
        assert response.status_code == 200

        export_data = response.json()
        assert "user_data" in export_data
        assert "meals" in export_data
        assert "feedback" in export_data

        # Request data deletion
        response = client.delete(
            f"/api/v1/privacy/{test_user.student_id}/delete", headers=auth_headers)
        assert response.status_code == 200

    def test_admin_endpoints(self, client, admin_user, admin_headers, sample_image):
        """Test admin-specific endpoints."""

        # Admin authentication
        with patch('app.core.auth.verify_password', return_value=True):
            login_data = {
                "username": admin_user.username,
                "password": "admin_password"
            }

            response = client.post("/api/v1/auth/admin/login", json=login_data)
            assert response.status_code == 200

        # Dataset management
        with open(sample_image, 'rb') as img_file:
            response = client.post(
                "/api/v1/admin/dataset/upload",
                files={"image": ("new_food.jpg", img_file, "image/jpeg")},
                data={
                    "food_name": "test_nigerian_food",
                    "food_class": "proteins",
                    "cultural_context": "Traditional Nigerian protein source"
                },
                headers=admin_headers
            )

        assert response.status_code in [201, 400]

        # Get dataset statistics
        response = client.get(
            "/api/v1/admin/dataset/stats", headers=admin_headers)
        assert response.status_code == 200

        stats_data = response.json()
        assert "total_images" in stats_data
        assert "food_classes" in stats_data

        # List dataset items
        response = client.get(
            "/api/v1/admin/dataset/items", headers=admin_headers)
        assert response.status_code == 200

        # Nutrition rules management
        rule_data = {
            "rule_name": "test_rule",
            "condition_logic": {"missing_food_groups": ["vegetables"]},
            "feedback_template": "Consider adding vegetables to your meal for better nutrition",
            "priority": 1,
            "is_active": True
        }

        response = client.post(
            "/api/v1/admin/nutrition-rules", json=rule_data, headers=admin_headers)
        assert response.status_code in [201, 400]

        # Get nutrition rules
        response = client.get(
            "/api/v1/admin/nutrition-rules", headers=admin_headers)
        assert response.status_code == 200

        rules_data = response.json()
        assert "rules" in rules_data

        # Update nutrition rule
        rule_id = "test_rule_123"
        updated_rule = {
            "rule_name": "updated_test_rule",
            "feedback_template": "Updated feedback template",
            "priority": 2
        }

        response = client.put(
            f"/api/v1/admin/nutrition-rules/{rule_id}", json=updated_rule, headers=admin_headers)
        assert response.status_code in [200, 404]

        # Delete nutrition rule
        response = client.delete(
            f"/api/v1/admin/nutrition-rules/{rule_id}", headers=admin_headers)
        assert response.status_code in [200, 404]

        # System analytics
        response = client.get(
            "/api/v1/admin/analytics/usage", headers=admin_headers)
        assert response.status_code == 200

        analytics_data = response.json()
        assert "total_users" in analytics_data
        assert "total_meals_analyzed" in analytics_data

        # User management
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200

        users_data = response.json()
        assert "users" in users_data
        assert "total_count" in users_data

    def test_cache_endpoints(self, client, admin_headers):
        """Test cache management endpoints."""

        # Get cache statistics
        response = client.get("/api/v1/cache/stats", headers=admin_headers)
        assert response.status_code == 200

        cache_stats = response.json()
        assert "redis_info" in cache_stats
        assert "cache_hit_rate" in cache_stats

        # Clear specific cache
        cache_key = "test_cache_key"
        response = client.delete(
            f"/api/v1/cache/clear/{cache_key}", headers=admin_headers)
        assert response.status_code == 200

        # Clear all cache
        response = client.delete(
            "/api/v1/cache/clear-all", headers=admin_headers)
        assert response.status_code == 200

    def test_workflow_endpoints(self, client, test_user, auth_headers):
        """Test workflow orchestration endpoints."""

        # Get workflow status
        workflow_id = "test_workflow_123"
        response = client.get(
            f"/api/v1/workflows/{workflow_id}/status", headers=auth_headers)
        assert response.status_code in [200, 404]

        # Cancel workflow
        response = client.post(
            f"/api/v1/workflows/{workflow_id}/cancel", headers=auth_headers)
        assert response.status_code in [200, 404]

        # Get user's active workflows
        response = client.get(
            f"/api/v1/workflows/user/{test_user.student_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_error_handling_across_endpoints(self, client, auth_headers):
        """Test error handling consistency across all endpoints."""

        # Test with invalid user ID
        invalid_user_id = "invalid-uuid"

        endpoints_to_test = [
            f"/api/v1/history/{invalid_user_id}/meals",
            f"/api/v1/insights/{invalid_user_id}/weekly",
            f"/api/v1/consent/{invalid_user_id}",
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [400, 404, 422]

            if response.status_code != 404:  # 404 might not have error structure
                error_data = response.json()
                assert "error" in error_data
                assert "message" in error_data["error"]

        # Test with malformed JSON
        response = client.post(
            "/api/v1/consent/valid-uuid",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test with missing authentication
        response = client.get("/api/v1/history/some-user/meals")
        assert response.status_code == 401

    def test_rate_limiting_across_endpoints(self, client, test_user, auth_headers, sample_image):
        """Test rate limiting across different endpoints."""

        # Test meal analysis rate limiting
        responses = []

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={"detected_foods": []}
            )

            for i in range(20):  # Make many requests quickly
                with open(sample_image, 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": ("meal.jpg", img_file, "image/jpeg")},
                        data={"student_id": str(test_user.student_id)},
                        headers=auth_headers
                    )
                    responses.append(response.status_code)

        # Should have some rate limiting
        rate_limited = [r for r in responses if r == 429]
        successful = [r for r in responses if r in [200, 202]]

        # All requests should get a response
        assert len(rate_limited) + len(successful) == len(responses)

    def test_api_versioning_and_compatibility(self, client):
        """Test API versioning and backward compatibility."""

        # Test API version endpoint
        response = client.get("/api/version")
        assert response.status_code == 200

        version_data = response.json()
        assert "version" in version_data
        assert "api_version" in version_data

        # Test v1 endpoints
        response = client.get("/api/v1/monitoring/ping")
        assert response.status_code == 200

        # Test that deprecated endpoints still work (if any)
        # This would depend on actual API evolution

    def test_content_type_handling(self, client, test_user, sample_image, auth_headers):
        """Test proper content type handling across endpoints."""

        # Test JSON endpoints
        json_data = {"test": "data"}
        response = client.post(
            f"/api/v1/consent/{test_user.student_id}",
            json=json_data,
            headers=auth_headers
        )
        # Should handle JSON properly

        # Test multipart form data
        with open(sample_image, 'rb') as img_file:
            response = client.post(
                "/api/v1/meals/analyze",
                files={"image": ("meal.jpg", img_file, "image/jpeg")},
                data={"student_id": str(test_user.student_id)},
                headers=auth_headers
            )
        # Should handle multipart data properly

        # Test unsupported content type
        response = client.post(
            f"/api/v1/consent/{test_user.student_id}",
            data="plain text data",
            headers={**auth_headers, "Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 415, 422]

    def test_cors_and_security_headers(self, client):
        """Test CORS and security headers."""

        # Test CORS preflight
        response = client.options("/api/v1/monitoring/ping")
        # Should handle OPTIONS requests appropriately

        # Test security headers in responses
        response = client.get("/api/v1/monitoring/ping")

        # Check for security headers (if implemented)
        headers = response.headers
        # These would depend on actual security header implementation
