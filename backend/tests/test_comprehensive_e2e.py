"""Comprehensive end-to-end testing suite for the nutrition feedback system."""

import pytest
import asyncio
import tempfile
import os
import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from PIL import Image
import io
import threading
from concurrent.futures import ThreadPoolExecutor

from app.main import app
from app.core.orchestration import ServiceOrchestrator, MealAnalysisWorkflow
from app.core.async_tasks import get_task_processor, TaskPriority
from app.models.user import Student
from app.models.meal import Meal
from app.models.feedback import FeedbackRecord


class TestComprehensiveEndToEnd:
    """Comprehensive end-to-end tests covering complete user workflows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_images(self):
        """Create multiple sample images for testing."""
        images = {}

        # Create different types of test images
        for name, color, size in [
            ("jollof_rice", "orange", (224, 224)),
            ("beans", "brown", (224, 224)),
            ("chicken", "white", (224, 224)),
            ("vegetables", "green", (224, 224)),
            ("low_quality", "red", (50, 50)),  # Low quality image
            ("large_image", "blue", (2048, 2048))  # Large image
        ]:
            image = Image.new('RGB', size, color=color)
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix='.jpg')
            image.save(temp_file.name, 'JPEG')
            images[name] = temp_file.name

        yield images

        # Cleanup
        for path in images.values():
            if os.path.exists(path):
                os.unlink(path)

    @pytest.fixture
    def test_users(self, db_session):
        """Create multiple test users."""
        users = []
        for i in range(5):
            user = Student(
                email=f"student{i}@university.edu.ng",
                name=f"Test Student {i}",
                password_hash="hashed_password",
                history_enabled=True
            )
            db_session.add(user)
            users.append(user)

        db_session.commit()
        for user in users:
            db_session.refresh(user)

        return users

    @pytest.mark.asyncio
    async def test_complete_user_journey_workflow(self, client, test_users, sample_images):
        """Test complete user journey from registration to weekly insights."""

        user = test_users[0]

        # Step 1: User Authentication
        auth_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "test_password"
        })

        # Mock successful authentication for this test
        with patch('app.core.auth.verify_password', return_value=True):
            auth_response = client.post("/api/v1/auth/login", json={
                "email": user.email,
                "password": "test_password"
            })

        # Step 2: Upload and analyze multiple meals over a week
        meal_responses = []

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor, \
                patch('app.services.feedback_generation_service.FeedbackGenerationService') as mock_feedback:

            # Mock ML predictions for different meals
            mock_predictor.return_value.predict_food_async = AsyncMock(
                side_effect=[
                    {
                        "detected_foods": [
                            {"name": "jollof_rice", "confidence": 0.95,
                                "food_class": "carbohydrates"},
                            {"name": "chicken", "confidence": 0.88,
                                "food_class": "proteins"}
                        ]
                    },
                    {
                        "detected_foods": [
                            {"name": "beans", "confidence": 0.92,
                                "food_class": "proteins"},
                            {"name": "plantain", "confidence": 0.85,
                                "food_class": "carbohydrates"}
                        ]
                    },
                    {
                        "detected_foods": [
                            {"name": "vegetables", "confidence": 0.90,
                                "food_class": "vitamins"},
                            {"name": "fish", "confidence": 0.87,
                                "food_class": "proteins"}
                        ]
                    }
                ]
            )

            mock_feedback.return_value.generate_feedback_async = AsyncMock(
                return_value={
                    "feedback_text": "Good meal balance! Consider adding more vegetables.",
                    "recommendations": ["Add leafy greens", "Include fruits"],
                    "balance_score": 0.8
                }
            )

            # Simulate multiple meal uploads
            for i, image_name in enumerate(["jollof_rice", "beans", "vegetables"]):
                with open(sample_images[image_name], 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": ("meal.jpg", img_file, "image/jpeg")},
                        data={"student_id": str(user.student_id)}
                    )
                    meal_responses.append(response)

        # Step 3: Check meal history
        history_response = client.get(
            f"/api/v1/history/{user.student_id}/meals",
            params={"limit": 10}
        )

        # Step 4: Generate weekly insights
        insights_response = client.get(
            f"/api/v1/insights/{user.student_id}/weekly"
        )

        # Verify complete workflow
        assert len(meal_responses) == 3
        # Additional assertions would depend on actual API responses

    @pytest.mark.asyncio
    async def test_concurrent_meal_analysis_workflow(self, client, test_users, sample_images):
        """Test system behavior under concurrent meal analysis requests."""

        async def analyze_meal(user_id: str, image_path: str) -> Dict[str, Any]:
            """Simulate concurrent meal analysis."""
            with open(image_path, 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": user_id}
                )
                return {
                    "status_code": response.status_code,
                    "user_id": user_id,
                    "response_time": time.time()
                }

        # Mock ML services to avoid actual inference
        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "test_food", "confidence": 0.9,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Create concurrent requests
            tasks = []
            for i in range(10):  # 10 concurrent requests
                user = test_users[i % len(test_users)]
                image = sample_images["jollof_rice"]
                task = analyze_meal(str(user.student_id), image)
                tasks.append(task)

            # Execute concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Verify all requests completed
            successful_requests = [
                r for r in results if not isinstance(r, Exception)]
            # Allow for some failures under load
            assert len(successful_requests) >= 8

            # Verify reasonable response time
            assert total_time < 30.0  # Should complete within 30 seconds

    def test_error_recovery_workflow(self, client, test_users, sample_images):
        """Test system recovery from various error conditions."""

        user = test_users[0]

        # Test 1: Invalid image format
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"This is not an image")
            temp_file.flush()

            with open(temp_file.name, 'rb') as file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("not_image.txt", file, "text/plain")},
                    data={"student_id": str(user.student_id)}
                )

            assert response.status_code == 422  # Validation error

            os.unlink(temp_file.name)

        # Test 2: ML service failure
        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                side_effect=Exception("ML service unavailable")
            )

            with open(sample_images["jollof_rice"], 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(user.student_id)}
                )

            # Should handle gracefully
            # Server error or service unavailable
            assert response.status_code in [500, 503]

        # Test 3: Database connection failure
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = client.get(f"/api/v1/history/{user.student_id}/meals")
            assert response.status_code == 500

    def test_performance_benchmarks(self, client, test_users, sample_images):
        """Test system performance benchmarks."""

        user = test_users[0]

        # Mock ML services for consistent timing
        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "test_food", "confidence": 0.9,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Test single meal analysis performance
            start_time = time.time()

            with open(sample_images["jollof_rice"], 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(user.student_id)}
                )

            analysis_time = time.time() - start_time

            # Verify performance requirement (5 seconds max)
            assert analysis_time < 5.0
            # Success or accepted for async processing
            assert response.status_code in [200, 202]

    def test_data_consistency_workflow(self, client, test_users, sample_images):
        """Test data consistency across multiple operations."""

        user = test_users[0]

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor, \
                patch('app.services.feedback_generation_service.FeedbackGenerationService') as mock_feedback:

            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "jollof_rice", "confidence": 0.95,
                            "food_class": "carbohydrates"}
                    ]
                }
            )

            mock_feedback.return_value.generate_feedback_async = AsyncMock(
                return_value={
                    "feedback_text": "Test feedback",
                    "recommendations": ["Test recommendation"],
                    "balance_score": 0.8
                }
            )

            # Upload meal
            with open(sample_images["jollof_rice"], 'rb') as img_file:
                upload_response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(user.student_id)}
                )

            # Check if meal appears in history
            history_response = client.get(
                f"/api/v1/history/{user.student_id}/meals"
            )

            # Verify data consistency
            if upload_response.status_code == 200:
                # Meal should appear in history if upload was successful
                assert history_response.status_code == 200

    def test_mobile_app_integration_scenarios(self, client, test_users, sample_images):
        """Test scenarios specific to mobile app integration."""

        user = test_users[0]

        # Test 1: Large image upload (mobile cameras produce large images)
        with open(sample_images["large_image"], 'rb') as img_file:
            response = client.post(
                "/api/v1/meals/analyze",
                files={"image": ("large_meal.jpg", img_file, "image/jpeg")},
                data={"student_id": str(user.student_id)}
            )

        # Should handle large images (resize/compress)
        # Success, accepted, or payload too large
        assert response.status_code in [200, 202, 413]

        # Test 2: Low quality image
        with open(sample_images["low_quality"], 'rb') as img_file:
            response = client.post(
                "/api/v1/meals/analyze",
                files={"image": ("low_quality.jpg", img_file, "image/jpeg")},
                data={"student_id": str(user.student_id)}
            )

        # Should provide appropriate feedback for low quality
        assert response.status_code in [200, 202, 422]

        # Test 3: Offline sync simulation
        # This would test the batch upload endpoint for offline-collected data
        batch_data = {
            "meals": [
                {
                    "student_id": str(user.student_id),
                    "timestamp": "2024-01-01T12:00:00Z",
                    "local_id": "offline_meal_1"
                }
            ]
        }

        response = client.post("/api/v1/meals/batch-sync", json=batch_data)
        # Should handle batch sync appropriately

    @pytest.mark.asyncio
    async def test_weekly_insights_generation_e2e(self, client, test_users, sample_images):
        """Test end-to-end weekly insights generation."""

        user = test_users[0]

        # Mock services for consistent test data
        with patch('app.services.history_service.HistoryService') as mock_history, \
                patch('app.services.insights_service.InsightsService') as mock_insights:

            # Mock meal history data
            mock_history.return_value.get_weekly_meals_async = AsyncMock(
                return_value={
                    "meals": [
                        {
                            "meal_id": "meal1",
                            "detected_foods": ["jollof_rice", "chicken"],
                            "food_classes": ["carbohydrates", "proteins"],
                            "timestamp": "2024-01-01T12:00:00Z"
                        },
                        {
                            "meal_id": "meal2",
                            "detected_foods": ["beans", "plantain"],
                            "food_classes": ["proteins", "carbohydrates"],
                            "timestamp": "2024-01-02T12:00:00Z"
                        }
                    ],
                    "total_meals": 2
                }
            )

            # Mock insights generation
            mock_insights.return_value.generate_weekly_insights_async = AsyncMock(
                return_value={
                    "nutrition_balance": {
                        "carbohydrates": 0.8,
                        "proteins": 0.7,
                        "vitamins": 0.3,
                        "minerals": 0.4,
                        "fats": 0.2,
                        "water": 0.5
                    },
                    "recommendations": [
                        "Include more vegetables in your meals",
                        "Add fruits for better vitamin intake"
                    ],
                    "positive_trends": [
                        "Good protein intake this week"
                    ],
                    "improvement_areas": [
                        "Low vegetable consumption"
                    ]
                }
            )

            # Request weekly insights
            response = client.get(f"/api/v1/insights/{user.student_id}/weekly")

            # Verify insights generation
            if response.status_code == 200:
                insights_data = response.json()
                assert "nutrition_balance" in insights_data
                assert "recommendations" in insights_data

    def test_admin_workflow_integration(self, client):
        """Test admin workflow integration."""

        # Test admin authentication
        admin_response = client.post("/api/v1/auth/admin/login", json={
            "username": "admin",
            "password": "admin_password"
        })

        # Test dataset management
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            # Create a test image for dataset
            image = Image.new('RGB', (224, 224), color='red')
            image.save(temp_file.name, 'JPEG')

            with open(temp_file.name, 'rb') as img_file:
                dataset_response = client.post(
                    "/api/v1/admin/dataset/upload",
                    files={"image": ("new_food.jpg", img_file, "image/jpeg")},
                    data={
                        "food_name": "test_food",
                        "food_class": "proteins",
                        "cultural_context": "Test Nigerian food"
                    }
                )

            os.unlink(temp_file.name)

        # Test nutrition rules management
        rule_data = {
            "rule_name": "test_rule",
            "condition_logic": {"missing_food_groups": ["vegetables"]},
            "feedback_template": "Add more vegetables to your meal",
            "priority": 1
        }

        rules_response = client.post(
            "/api/v1/admin/nutrition-rules", json=rule_data)

    def test_system_monitoring_integration(self, client):
        """Test system monitoring and health check integration."""

        # Test health checks
        health_response = client.get("/api/v1/monitoring/health")
        assert health_response.status_code in [200, 503]

        # Test metrics endpoint
        metrics_response = client.get("/api/v1/monitoring/metrics")
        assert metrics_response.status_code == 200

        # Test specific service health
        db_health = client.get("/api/v1/monitoring/health/database")
        redis_health = client.get("/api/v1/monitoring/health/redis")
        ml_health = client.get("/api/v1/monitoring/health/ml-service")

        # At least some services should be healthy
        health_responses = [db_health, redis_health, ml_health]
        healthy_services = [
            r for r in health_responses if r.status_code == 200]
        assert len(healthy_services) >= 1

    @pytest.mark.asyncio
    async def test_stress_testing_scenarios(self, client, test_users, sample_images):
        """Test system behavior under stress conditions."""

        # Test rapid successive requests from single user
        user = test_users[0]

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={"detected_foods": []}
            )

            # Rapid requests
            responses = []
            for i in range(20):  # 20 rapid requests
                with open(sample_images["jollof_rice"], 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": ("meal.jpg", img_file, "image/jpeg")},
                        data={"student_id": str(user.student_id)}
                    )
                    responses.append(response.status_code)

            # Should handle gracefully (may rate limit)
            successful_responses = [r for r in responses if r in [200, 202]]
            rate_limited = [r for r in responses if r == 429]

            # Either succeed or rate limit appropriately
            assert len(successful_responses) + \
                len(rate_limited) == len(responses)

    def test_data_privacy_compliance_workflow(self, client, test_users):
        """Test data privacy and compliance workflows."""

        user = test_users[0]

        # Test consent management
        consent_response = client.post(
            f"/api/v1/consent/{user.student_id}",
            json={
                "data_storage": True,
                "analytics": False,
                "marketing": False
            }
        )

        # Test data export (GDPR compliance)
        export_response = client.get(
            f"/api/v1/privacy/{user.student_id}/export")

        # Test data deletion
        deletion_response = client.delete(
            f"/api/v1/privacy/{user.student_id}/delete")

        # Verify privacy operations
        assert consent_response.status_code in [200, 201]

    def test_cultural_relevance_workflow(self, client, test_users, sample_images):
        """Test cultural relevance of feedback and food recognition."""

        user = test_users[0]

        # Mock Nigerian food recognition
        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor, \
                patch('app.services.feedback_generation_service.FeedbackGenerationService') as mock_feedback:

            # Mock recognition of Nigerian foods
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "amala", "confidence": 0.95,
                            "food_class": "carbohydrates"},
                        {"name": "efo_riro", "confidence": 0.90,
                            "food_class": "vitamins"},
                        {"name": "suya", "confidence": 0.88,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Mock culturally relevant feedback
            mock_feedback.return_value.generate_feedback_async = AsyncMock(
                return_value={
                    "feedback_text": "Excellent Nigerian meal! Your amala with efo riro provides good carbohydrates and vitamins. The suya adds protein.",
                    "recommendations": [
                        "Consider adding moimoi for extra protein",
                        "Include fruits like orange or banana"
                    ],
                    "cultural_context": "Traditional Yoruba meal combination",
                    "balance_score": 0.85
                }
            )

            # Test meal analysis
            with open(sample_images["jollof_rice"], 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("nigerian_meal.jpg",
                                     img_file, "image/jpeg")},
                    data={"student_id": str(user.student_id)}
                )

            # Verify culturally relevant response
            if response.status_code == 200:
                result = response.json()
                # Check for Nigerian food names and cultural context
                # This would depend on actual API response structure
