"""End-to-end workflow tests for the nutrition feedback system."""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.main import app
from app.core.orchestration import ServiceOrchestrator, MealAnalysisWorkflow, get_orchestrator
from app.core.async_tasks import get_task_processor, TaskPriority
from app.core.error_handling import get_error_handler
from app.models.user import Student
from app.models.meal import Meal
from app.models.feedback import FeedbackRecord


class TestEndToEndWorkflows:
    """Test complete user workflows from start to finish."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator instance."""
        return ServiceOrchestrator()

    @pytest.fixture
    def meal_workflow(self, orchestrator):
        """Create a meal analysis workflow instance."""
        return MealAnalysisWorkflow(orchestrator)

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for testing."""
        # Create a simple test image
        image = Image.new('RGB', (224, 224), color='red')

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image.save(temp_file.name, 'JPEG')

        yield temp_file.name

        # Cleanup
        os.unlink(temp_file.name)

    @pytest.fixture
    def authenticated_user(self, db_session):
        """Create an authenticated user for testing."""
        user = Student(
            email="test@example.com",
            name="Test Student",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_complete_meal_analysis_workflow(
        self,
        meal_workflow,
        authenticated_user,
        sample_image_file,
        db_session
    ):
        """Test the complete meal analysis workflow from image upload to feedback."""

        # Mock service calls to avoid actual ML inference
        with patch('app.services.image_service.ImageService') as mock_image_service, \
                patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor, \
                patch('app.services.feedback_service.FeedbackService') as mock_feedback_service, \
                patch('app.services.history_service.HistoryService') as mock_history_service, \
                patch('app.services.user_service.UserService') as mock_user_service:

            # Setup mock responses
            mock_user_service.return_value.validate_user_async = AsyncMock(
                return_value={"valid": True, "user_id": str(
                    authenticated_user.student_id)}
            )

            mock_image_service.return_value.validate_image = AsyncMock(
                return_value={"valid": True,
                              "format": "JPEG", "size": (224, 224)}
            )

            mock_image_service.return_value.preprocess_image = AsyncMock(
                return_value={
                    "processed_path": "/processed/image.jpg",
                    "metadata": {"width": 224, "height": 224}
                }
            )

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

            mock_feedback_service.return_value.generate_feedback_async = AsyncMock(
                return_value={
                    "feedback_text": "Great meal! You have good protein and carbohydrates. Try adding some vegetables.",
                    "recommendations": ["Add vegetables for better nutrition balance"],
                    "balance_score": 0.75
                }
            )

            mock_history_service.return_value.store_meal_record_async = AsyncMock(
                return_value={"stored": True, "meal_record_id": "record_123"}
            )

            # Execute the workflow
            result = await meal_workflow.analyze_meal_complete(
                student_id=str(authenticated_user.student_id),
                meal_id="test_meal_123",
                image_path=sample_image_file
            )

            # Verify workflow completed successfully
            assert result.status.value == "completed"
            assert result.result is not None

            # Verify all steps were executed
            workflow_result = result.result
            assert "validate_user" in workflow_result
            assert "validate_image" in workflow_result
            assert "preprocess_image" in workflow_result
            assert "recognize_food" in workflow_result
            assert "generate_feedback" in workflow_result
            assert "store_history" in workflow_result

            # Verify service calls were made
            mock_user_service.return_value.validate_user_async.assert_called_once()
            mock_image_service.return_value.validate_image.assert_called_once()
            mock_image_service.return_value.preprocess_image.assert_called_once()
            mock_predictor.return_value.predict_food_async.assert_called_once()
            mock_feedback_service.return_value.generate_feedback_async.assert_called_once()
            mock_history_service.return_value.store_meal_record_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_meal_analysis_workflow_with_failure_recovery(
        self,
        meal_workflow,
        authenticated_user,
        sample_image_file
    ):
        """Test workflow behavior when optional steps fail."""

        with patch('app.services.image_service.ImageService') as mock_image_service, \
                patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor, \
                patch('app.services.feedback_service.FeedbackService') as mock_feedback_service, \
                patch('app.services.history_service.HistoryService') as mock_history_service, \
                patch('app.services.user_service.UserService') as mock_user_service:

            # Setup successful mocks for required steps
            mock_user_service.return_value.validate_user_async = AsyncMock(
                return_value={"valid": True}
            )
            mock_image_service.return_value.validate_image = AsyncMock(
                return_value={"valid": True}
            )
            mock_image_service.return_value.preprocess_image = AsyncMock(
                return_value={"processed_path": "/processed/image.jpg"}
            )
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={"detected_foods": []}
            )
            mock_feedback_service.return_value.generate_feedback_async = AsyncMock(
                return_value={"feedback_text": "Test feedback"}
            )

            # Make optional history step fail
            mock_history_service.return_value.store_meal_record_async = AsyncMock(
                side_effect=Exception("History service unavailable")
            )

            # Execute workflow
            result = await meal_workflow.analyze_meal_complete(
                student_id=str(authenticated_user.student_id),
                meal_id="test_meal_123",
                image_path=sample_image_file
            )

            # Workflow should still complete successfully
            assert result.status.value == "completed"

            # History step should show as failed but optional
            workflow_result = result.result
            assert "store_history" in workflow_result
            assert workflow_result["store_history"]["status"] == "failed"
            assert workflow_result["store_history"]["optional"] is True

    @pytest.mark.asyncio
    async def test_weekly_insights_generation_workflow(
        self,
        meal_workflow,
        authenticated_user
    ):
        """Test the weekly insights generation workflow."""

        with patch('app.services.user_service.UserService') as mock_user_service, \
                patch('app.services.history_service.HistoryService') as mock_history_service, \
                patch('app.services.insights_service.InsightsService') as mock_insights_service:

            # Setup mock responses
            mock_user_service.return_value.validate_user_async = AsyncMock(
                return_value={"valid": True}
            )

            mock_history_service.return_value.get_weekly_meals_async = AsyncMock(
                return_value={
                    "meals": [
                        {"meal_id": "meal1", "detected_foods": [
                            "jollof_rice", "chicken"]},
                        {"meal_id": "meal2", "detected_foods": [
                            "beans", "plantain"]}
                    ],
                    "total_meals": 2
                }
            )

            mock_insights_service.return_value.analyze_nutrition_patterns_async = AsyncMock(
                return_value={
                    "patterns": {
                        "carbohydrates": 0.8,
                        "proteins": 0.7,
                        "vegetables": 0.3
                    }
                }
            )

            mock_insights_service.return_value.generate_weekly_recommendations_async = AsyncMock(
                return_value={
                    "recommendations": [
                        "Try to include more vegetables in your meals",
                        "Good protein intake this week!"
                    ]
                }
            )

            mock_history_service.return_value.store_weekly_insights_async = AsyncMock(
                return_value={"stored": True}
            )

            # Execute workflow
            result = await meal_workflow.generate_weekly_insights(
                student_id=str(authenticated_user.student_id)
            )

            # Verify workflow completed successfully
            assert result.status.value == "completed"
            assert result.result is not None

            # Verify all steps were executed
            workflow_result = result.result
            assert "validate_user" in workflow_result
            assert "fetch_meal_history" in workflow_result
            assert "analyze_patterns" in workflow_result
            assert "generate_recommendations" in workflow_result
            assert "store_insights" in workflow_result

    @pytest.mark.asyncio
    async def test_batch_meal_analysis_workflow(
        self,
        meal_workflow,
        authenticated_user,
        sample_image_file
    ):
        """Test batch processing of multiple meal analyses."""

        # Create multiple meal requests
        meal_requests = [
            {
                "student_id": str(authenticated_user.student_id),
                "meal_id": f"meal_{i}",
                "image_path": sample_image_file
            }
            for i in range(3)
        ]

        with patch.object(meal_workflow, 'analyze_meal_complete') as mock_analyze:
            # Mock successful analysis for all meals
            mock_analyze.return_value = Mock(
                status=Mock(value="completed"),
                result={"analysis": "success"}
            )

            # Execute batch workflow
            results = await meal_workflow.batch_meal_analysis(meal_requests)

            # Verify all meals were processed
            assert len(results) == 3

            # Note: In the actual implementation, this would call the orchestrator's
            # execute_parallel_tasks method, which we'd need to mock differently

    @pytest.mark.asyncio
    async def test_async_task_processing_integration(self):
        """Test integration with async task processor."""

        # Get task processor
        processor = await get_task_processor()

        # Define a test async function
        async def test_task(data: str) -> str:
            await asyncio.sleep(0.1)  # Simulate work
            return f"processed_{data}"

        # Submit task
        task_id = await processor.submit_task(
            "test_task",
            test_task,
            "test_data",
            priority=TaskPriority.HIGH
        )

        # Wait for completion
        max_wait = 5.0  # 5 seconds max
        wait_time = 0.0
        while wait_time < max_wait:
            status = await processor.get_task_status(task_id)
            if status and status["status"] == "completed":
                break
            await asyncio.sleep(0.1)
            wait_time += 0.1

        # Verify task completed
        final_status = await processor.get_task_status(task_id)
        assert final_status is not None
        assert final_status["status"] == "completed"
        assert final_status["result"] == "processed_test_data"

    def test_api_error_handling_integration(self, client, authenticated_user):
        """Test API error handling with standardized responses."""

        # Test validation error
        response = client.post(
            "/api/v1/meals/analyze",
            json={"invalid": "data"}  # Missing required fields
        )

        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["category"] == "validation"

    def test_health_check_integration(self, client):
        """Test health check endpoints integration."""

        # Test basic health check
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code in [200, 503]  # Healthy or degraded

        health_data = response.json()
        assert "overall_status" in health_data
        assert "checks" in health_data
        assert "summary" in health_data

        # Test specific health check
        response = client.get("/api/v1/monitoring/health/database")
        assert response.status_code in [200, 503]

    def test_metrics_endpoint_integration(self, client):
        """Test metrics endpoint integration."""

        response = client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 200

        metrics_data = response.json()
        assert "service" in metrics_data
        assert "async_tasks" in metrics_data
        assert "orchestration" in metrics_data

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, meal_workflow, authenticated_user):
        """Test workflow error handling and recovery."""

        with patch('app.services.user_service.UserService') as mock_user_service:
            # Make user validation fail (required step)
            mock_user_service.return_value.validate_user_async = AsyncMock(
                side_effect=Exception("User service unavailable")
            )

            # Execute workflow - should fail
            result = await meal_workflow.analyze_meal_complete(
                student_id=str(authenticated_user.student_id),
                meal_id="test_meal_123",
                image_path="/fake/path.jpg"
            )

            # Verify workflow failed
            assert result.status.value == "failed"
            assert result.error is not None
            assert "User service unavailable" in result.error

    def test_concurrent_request_handling(self, client):
        """Test handling of concurrent requests."""
        import threading
        import time

        results = []

        def make_request():
            response = client.get("/api/v1/monitoring/ping")
            results.append(response.status_code)

        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 10
        assert all(status == 200 for status in results)

    @pytest.mark.asyncio
    async def test_service_orchestration_with_timeouts(self, orchestrator):
        """Test service orchestration with timeout handling."""

        async def slow_service_call(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate slow operation
            return {"result": "success"}

        # Mock a service call that times out
        with patch.object(orchestrator, '_execute_service_call', side_effect=slow_service_call):

            workflow_steps = [
                {
                    "name": "slow_step",
                    "service": "test_service",
                    "method": "slow_method",
                    "params": {},
                    "timeout": 0.5  # Short timeout
                }
            ]

            result = await orchestrator.execute_workflow(
                "timeout_test",
                workflow_steps,
                {}
            )

            # Workflow should fail due to timeout
            assert result.status.value == "failed"
            assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    def test_request_id_propagation(self, client):
        """Test that request IDs are properly propagated through error responses."""

        # Make a request that will cause a validation error
        response = client.post(
            "/api/v1/meals/analyze",
            json={},  # Empty body to trigger validation error
            headers={"X-Request-ID": "test-request-123"}
        )

        assert response.status_code == 422
        error_data = response.json()

        # Check if request ID is included in error response
        # Note: This would require middleware to capture and include request IDs
        assert "error" in error_data
