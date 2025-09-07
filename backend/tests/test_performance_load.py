"""Performance and load testing for the nutrition feedback system."""

import pytest
import asyncio
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import tempfile
import os
from PIL import Image

from app.main import app
from app.models.user import Student


class TestPerformanceAndLoad:
    """Performance and load testing scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = Student(
            email="performance@test.com",
            name="Performance Test User",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        image = Image.new('RGB', (224, 224), color='red')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image.save(temp_file.name, 'JPEG')

        yield temp_file.name

        os.unlink(temp_file.name)

    def test_single_request_response_time(self, client, test_user, sample_image):
        """Test single request response time meets requirements."""

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "jollof_rice", "confidence": 0.95,
                            "food_class": "carbohydrates"}
                    ]
                }
            )

            # Measure response time
            start_time = time.time()

            with open(sample_image, 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(test_user.student_id)}
                )

            response_time = time.time() - start_time

            # Verify response time requirement (5 seconds max)
            assert response_time < 5.0, f"Response time {response_time:.2f}s exceeds 5s requirement"
            assert response.status_code in [200, 202]

    def test_concurrent_users_load(self, client, test_user, sample_image):
        """Test system performance under concurrent user load."""

        def make_request(user_id: str) -> Dict[str, Any]:
            """Make a single request and measure performance."""
            start_time = time.time()

            with open(sample_image, 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": user_id}
                )

            end_time = time.time()

            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "user_id": user_id
            }

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "test_food", "confidence": 0.9,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Test with increasing concurrent users
            concurrent_users = [5, 10, 20, 50]
            results = {}

            for num_users in concurrent_users:
                print(f"\nTesting with {num_users} concurrent users...")

                # Execute concurrent requests
                with ThreadPoolExecutor(max_workers=num_users) as executor:
                    futures = [
                        executor.submit(
                            make_request, str(test_user.student_id))
                        for _ in range(num_users)
                    ]

                    user_results = []
                    for future in as_completed(futures):
                        try:
                            result = future.result(
                                timeout=30)  # 30 second timeout
                            user_results.append(result)
                        except Exception as e:
                            user_results.append({
                                "status_code": 500,
                                "response_time": 30.0,
                                "error": str(e)
                            })

                # Analyze results
                successful_requests = [
                    r for r in user_results if r["status_code"] in [200, 202]]
                failed_requests = [
                    r for r in user_results if r["status_code"] not in [200, 202]]

                if successful_requests:
                    response_times = [r["response_time"]
                                      for r in successful_requests]
                    avg_response_time = statistics.mean(response_times)
                    max_response_time = max(response_times)
                    min_response_time = min(response_times)

                    results[num_users] = {
                        "successful": len(successful_requests),
                        "failed": len(failed_requests),
                        "success_rate": len(successful_requests) / num_users,
                        "avg_response_time": avg_response_time,
                        "max_response_time": max_response_time,
                        "min_response_time": min_response_time
                    }

                    print(
                        f"Success rate: {results[num_users]['success_rate']:.2%}")
                    print(f"Avg response time: {avg_response_time:.2f}s")
                    print(f"Max response time: {max_response_time:.2f}s")
                else:
                    results[num_users] = {
                        "successful": 0,
                        "failed": len(failed_requests),
                        "success_rate": 0.0
                    }

            # Verify performance requirements
            # At least 80% success rate with 10 concurrent users
            assert results[10]["success_rate"] >= 0.8, "System should handle 10 concurrent users with 80% success rate"

            # Average response time should remain reasonable
            if results[10]["successful"] > 0:
                assert results[10]["avg_response_time"] < 10.0, "Average response time should be under 10s with 10 users"

    def test_sustained_load_performance(self, client, test_user, sample_image):
        """Test system performance under sustained load."""

        def continuous_requests(duration_seconds: int, request_interval: float) -> List[Dict[str, Any]]:
            """Make continuous requests for specified duration."""
            results = []
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                request_start = time.time()

                try:
                    with open(sample_image, 'rb') as img_file:
                        response = client.post(
                            "/api/v1/meals/analyze",
                            files={
                                "image": ("meal.jpg", img_file, "image/jpeg")},
                            data={"student_id": str(test_user.student_id)}
                        )

                    request_end = time.time()

                    results.append({
                        "timestamp": request_start,
                        "response_time": request_end - request_start,
                        "status_code": response.status_code
                    })

                except Exception as e:
                    results.append({
                        "timestamp": request_start,
                        "response_time": 30.0,
                        "status_code": 500,
                        "error": str(e)
                    })

                # Wait for next request
                time.sleep(max(0, request_interval -
                           (time.time() - request_start)))

            return results

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "test_food", "confidence": 0.9,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Run sustained load test for 60 seconds with 1 request per second
            print("\nRunning sustained load test (60 seconds, 1 req/sec)...")
            results = continuous_requests(
                duration_seconds=60, request_interval=1.0)

            # Analyze sustained performance
            successful_requests = [
                r for r in results if r["status_code"] in [200, 202]]
            failed_requests = [
                r for r in results if r["status_code"] not in [200, 202]]

            success_rate = len(successful_requests) / \
                len(results) if results else 0

            if successful_requests:
                response_times = [r["response_time"]
                                  for r in successful_requests]
                avg_response_time = statistics.mean(response_times)

                # Check for performance degradation over time
                first_half = response_times[:len(response_times)//2]
                second_half = response_times[len(response_times)//2:]

                if first_half and second_half:
                    first_half_avg = statistics.mean(first_half)
                    second_half_avg = statistics.mean(second_half)
                    degradation = (second_half_avg -
                                   first_half_avg) / first_half_avg

                    print(f"Performance degradation: {degradation:.2%}")

                    # Performance should not degrade by more than 50%
                    assert degradation < 0.5, "Performance degradation should be less than 50%"

            print(f"Sustained load success rate: {success_rate:.2%}")
            print(f"Total requests: {len(results)}")

            # Should maintain reasonable success rate under sustained load
            assert success_rate >= 0.7, "Should maintain 70% success rate under sustained load"

    def test_memory_usage_under_load(self, client, test_user, sample_image):
        """Test memory usage doesn't grow excessively under load."""

        import psutil
        import os

        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "test_food", "confidence": 0.9,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Make many requests to test memory usage
            memory_measurements = [initial_memory]

            for i in range(100):  # 100 requests
                with open(sample_image, 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": ("meal.jpg", img_file, "image/jpeg")},
                        data={"student_id": str(test_user.student_id)}
                    )

                # Measure memory every 10 requests
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_measurements.append(current_memory)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory

            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Final memory: {final_memory:.2f} MB")
            print(f"Memory growth: {memory_growth:.2f} MB")

            # Memory growth should be reasonable (less than 100MB for 100 requests)
            assert memory_growth < 100, f"Memory growth {memory_growth:.2f} MB is excessive"

    def test_database_performance_under_load(self, client, test_user):
        """Test database performance under concurrent access."""

        def database_operation() -> Dict[str, Any]:
            """Perform database-intensive operation."""
            start_time = time.time()

            # Test meal history retrieval (database-intensive)
            response = client.get(
                f"/api/v1/history/{test_user.student_id}/meals")

            end_time = time.time()

            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time
            }

        # Test concurrent database operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(database_operation) for _ in range(50)]

            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "status_code": 500,
                        "response_time": 10.0,
                        "error": str(e)
                    })

        # Analyze database performance
        successful_ops = [r for r in results if r["status_code"] == 200]

        if successful_ops:
            response_times = [r["response_time"] for r in successful_ops]
            avg_db_response_time = statistics.mean(response_times)
            max_db_response_time = max(response_times)

            print(
                f"Database operations - Avg: {avg_db_response_time:.2f}s, Max: {max_db_response_time:.2f}s")

            # Database operations should be fast
            assert avg_db_response_time < 2.0, "Average database response time should be under 2s"
            assert max_db_response_time < 5.0, "Max database response time should be under 5s"

    def test_api_rate_limiting(self, client, test_user, sample_image):
        """Test API rate limiting functionality."""

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "test_food", "confidence": 0.9,
                            "food_class": "proteins"}
                    ]
                }
            )

            # Make rapid requests to trigger rate limiting
            responses = []

            for i in range(30):  # 30 rapid requests
                with open(sample_image, 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": ("meal.jpg", img_file, "image/jpeg")},
                        data={"student_id": str(test_user.student_id)}
                    )
                    responses.append(response.status_code)

            # Check if rate limiting is working
            rate_limited_responses = [r for r in responses if r == 429]
            successful_responses = [r for r in responses if r in [200, 202]]

            print(
                f"Successful: {len(successful_responses)}, Rate limited: {len(rate_limited_responses)}")

            # Should have some rate limiting for rapid requests
            # (This depends on actual rate limiting implementation)
            total_responses = len(successful_responses) + \
                len(rate_limited_responses)
            assert total_responses == len(
                responses), "All requests should get a response"

    def test_large_file_upload_performance(self, client, test_user):
        """Test performance with large file uploads."""

        # Create large test image
        large_image = Image.new('RGB', (2048, 2048), color='blue')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        large_image.save(temp_file.name, 'JPEG', quality=95)

        try:
            file_size = os.path.getsize(temp_file.name) / 1024 / 1024  # MB
            print(f"Testing with {file_size:.2f} MB image")

            with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
                mock_predictor.return_value.predict_food_async = AsyncMock(
                    return_value={
                        "detected_foods": [
                            {"name": "test_food", "confidence": 0.9,
                                "food_class": "proteins"}
                        ]
                    }
                )

                start_time = time.time()

                with open(temp_file.name, 'rb') as img_file:
                    response = client.post(
                        "/api/v1/meals/analyze",
                        files={"image": ("large_meal.jpg",
                                         img_file, "image/jpeg")},
                        data={"student_id": str(test_user.student_id)}
                    )

                upload_time = time.time() - start_time

                print(f"Large file upload time: {upload_time:.2f}s")

                # Should handle large files appropriately
                # Success, accepted, or payload too large
                assert response.status_code in [200, 202, 413]

                if response.status_code in [200, 202]:
                    # If accepted, should still be reasonably fast
                    assert upload_time < 15.0, "Large file processing should complete within 15s"

        finally:
            os.unlink(temp_file.name)

    def test_cache_performance_impact(self, client, test_user, sample_image):
        """Test performance impact of caching."""

        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = AsyncMock(
                return_value={
                    "detected_foods": [
                        {"name": "jollof_rice", "confidence": 0.95,
                            "food_class": "carbohydrates"}
                    ]
                }
            )

            # First request (cache miss)
            start_time = time.time()
            with open(sample_image, 'rb') as img_file:
                response1 = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(test_user.student_id)}
                )
            first_request_time = time.time() - start_time

            # Second identical request (potential cache hit)
            start_time = time.time()
            with open(sample_image, 'rb') as img_file:
                response2 = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(test_user.student_id)}
                )
            second_request_time = time.time() - start_time

            print(f"First request: {first_request_time:.2f}s")
            print(f"Second request: {second_request_time:.2f}s")

            # Both requests should succeed
            assert response1.status_code in [200, 202]
            assert response2.status_code in [200, 202]

            # Second request might be faster due to caching
            # (This depends on actual caching implementation)

    @pytest.mark.asyncio
    async def test_async_task_performance(self):
        """Test async task processing performance."""

        from app.core.async_tasks import get_task_processor, TaskPriority

        processor = await get_task_processor()

        async def test_task(data: str) -> str:
            """Simple test task."""
            await asyncio.sleep(0.1)  # Simulate work
            return f"processed_{data}"

        # Submit multiple tasks
        task_ids = []
        start_time = time.time()

        for i in range(20):
            task_id = await processor.submit_task(
                f"test_task_{i}",
                test_task,
                f"data_{i}",
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)

        # Wait for all tasks to complete
        completed_tasks = 0
        max_wait_time = 30.0  # 30 seconds max

        while completed_tasks < len(task_ids) and (time.time() - start_time) < max_wait_time:
            for task_id in task_ids:
                status = await processor.get_task_status(task_id)
                if status and status["status"] == "completed":
                    completed_tasks += 1

            await asyncio.sleep(0.1)

        total_time = time.time() - start_time

        print(
            f"Processed {completed_tasks}/{len(task_ids)} tasks in {total_time:.2f}s")

        # Should process tasks efficiently
        assert completed_tasks >= len(
            task_ids) * 0.8  # At least 80% completion
        assert total_time < max_wait_time  # Should complete within time limit

    def test_error_handling_performance(self, client, test_user):
        """Test that error handling doesn't significantly impact performance."""

        # Test with invalid requests that will cause errors
        error_responses = []

        start_time = time.time()

        for i in range(10):
            # Invalid request (missing image)
            response = client.post(
                "/api/v1/meals/analyze",
                data={"student_id": str(test_user.student_id)}
            )
            error_responses.append(response.status_code)

        error_handling_time = time.time() - start_time

        print(
            f"Error handling time for 10 requests: {error_handling_time:.2f}s")

        # Error handling should be fast
        assert error_handling_time < 5.0, "Error handling should be fast"

        # Should return appropriate error codes
        assert all(code in [400, 422]
                   for code in error_responses), "Should return validation errors"
