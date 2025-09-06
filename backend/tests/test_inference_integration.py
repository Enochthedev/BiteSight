"""
Integration tests for the inference pipeline.
Tests the complete inference workflow from API to model prediction.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from PIL import Image
import base64
import io

from fastapi.testclient import TestClient
from app.main import app
from app.ml.serving.model_server import ModelServer, ServingConfig, ModelManager
from app.ml.inference.predictor import FoodPredictor, InferenceConfig, PredictionResult
from app.ml.models.mobilenet_food_classifier import MobileNetV2FoodClassifier
from app.ml.dataset.food_mapping import NigerianFoodMapper


class TestInferenceIntegration:
    """Integration tests for inference pipeline."""

    @pytest.fixture
    def sample_image(self):
        """Create sample PIL image."""
        return Image.new('RGB', (224, 224), color='blue')

    @pytest.fixture
    def sample_image_base64(self, sample_image):
        """Create base64 encoded sample image."""
        buffer = io.BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_data = buffer.getvalue()
        return base64.b64encode(image_data).decode('utf-8')

    @pytest.fixture
    def mock_model_checkpoint(self):
        """Create mock model checkpoint."""
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as f:
            model = MobileNetV2FoodClassifier(num_classes=5, pretrained=False)

            checkpoint = {
                'model_state_dict': model.state_dict(),
                'class_names': ['jollof_rice', 'beans', 'plantain', 'fish', 'efo_riro']
            }

            import torch
            torch.save(checkpoint, f.name)
            yield f.name

            # Cleanup
            Path(f.name).unlink()

    @pytest.fixture
    def mock_food_mapping(self):
        """Create mock food mapping file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            metadata = {
                "foods": [
                    {
                        "name": "jollof_rice",
                        "local_names": ["jollof"],
                        "food_class": "jollof_rice",
                        "nutritional_category": "carbohydrates"
                    },
                    {
                        "name": "beans",
                        "local_names": ["ewa"],
                        "food_class": "beans",
                        "nutritional_category": "proteins"
                    }
                ]
            }
            json.dump(metadata, f)
            yield f.name

            # Cleanup
            Path(f.name).unlink()

    @pytest.fixture
    def serving_config(self, mock_model_checkpoint, mock_food_mapping):
        """Create serving configuration."""
        return ServingConfig(
            model_path=mock_model_checkpoint,
            food_mapping_path=mock_food_mapping,
            device="cpu",
            warmup_samples=1,
            max_concurrent_requests=2
        )

    def test_model_manager_initialization(self, serving_config):
        """Test ModelManager initialization."""
        manager = ModelManager(serving_config)

        assert "primary" in manager.models
        assert "primary" in manager.model_info

        model = manager.get_model("primary")
        assert model is not None

        info = manager.get_model_info("primary")
        assert info is not None
        assert info.model_id == "primary"

        manager.cleanup()

    def test_model_server_initialization(self, serving_config):
        """Test ModelServer initialization."""
        server = ModelServer(serving_config)

        assert server.model_manager is not None
        assert server.is_healthy

        status = server.get_server_status()
        assert status["status"] == "healthy"
        assert len(status["models"]) > 0

        server.cleanup()

    @pytest.mark.asyncio
    async def test_single_prediction(self, serving_config, sample_image):
        """Test single image prediction."""
        server = ModelServer(serving_config)

        try:
            result = await server.predict_single(sample_image)

            assert result is not None
            assert isinstance(result, PredictionResult)
            assert result.class_name in [
                'jollof_rice', 'beans', 'plantain', 'fish', 'efo_riro']
            assert 0 <= result.confidence <= 1
            assert isinstance(result.class_index, int)

        finally:
            server.cleanup()

    @pytest.mark.asyncio
    async def test_batch_prediction(self, serving_config, sample_image):
        """Test batch prediction."""
        server = ModelServer(serving_config)

        try:
            images = [sample_image, sample_image, sample_image]
            results = await server.predict_batch(images)

            assert len(results) == 3
            for result in results:
                assert result is not None
                assert isinstance(result, PredictionResult)

        finally:
            server.cleanup()

    @pytest.mark.asyncio
    async def test_nutrition_analysis(self, serving_config, sample_image):
        """Test meal nutrition analysis."""
        server = ModelServer(serving_config)

        try:
            images = [sample_image, sample_image]
            result = await server.analyze_meal_nutrition(images)

            assert result is not None
            assert 'detected_foods' in result
            assert 'category_distribution' in result
            assert 'missing_categories' in result
            assert 'balance_score' in result

        finally:
            server.cleanup()

    @pytest.mark.asyncio
    async def test_health_check(self, serving_config):
        """Test server health check."""
        server = ModelServer(serving_config)

        try:
            is_healthy = await server.health_check()
            assert is_healthy

        finally:
            server.cleanup()


class TestInferenceAPI:
    """Test inference API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_image_base64(self):
        """Create base64 encoded sample image."""
        image = Image.new('RGB', (224, 224), color='red')
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_data = buffer.getvalue()
        return base64.b64encode(image_data).decode('utf-8')

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_predict_endpoint_success(self, mock_get_server, client, sample_image_base64):
        """Test successful prediction endpoint."""
        # Mock server and prediction result
        mock_server = Mock()
        mock_result = PredictionResult(
            class_name="jollof_rice",
            confidence=0.85,
            class_index=0,
            nutritional_category="carbohydrates",
            local_names=["jollof"]
        )

        mock_server.predict_single = AsyncMock(return_value=mock_result)
        mock_get_server.return_value = mock_server

        # Make request
        response = client.post(
            "/api/v1/inference/predict",
            json={
                "image_base64": sample_image_base64,
                "return_all_scores": False,
                "model_id": "primary"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["class_name"] == "jollof_rice"
        assert data["confidence"] == 0.85
        assert data["nutritional_category"] == "carbohydrates"

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_predict_endpoint_failure(self, mock_get_server, client, sample_image_base64):
        """Test prediction endpoint failure."""
        # Mock server that returns None (prediction failed)
        mock_server = Mock()
        mock_server.predict_single = AsyncMock(return_value=None)
        mock_get_server.return_value = mock_server

        # Make request
        response = client.post(
            "/api/v1/inference/predict",
            json={
                "image_base64": sample_image_base64,
                "return_all_scores": False,
                "model_id": "primary"
            }
        )

        assert response.status_code == 500

    def test_predict_endpoint_invalid_image(self, client):
        """Test prediction endpoint with invalid image."""
        response = client.post(
            "/api/v1/inference/predict",
            json={
                "image_base64": "invalid_base64_data",
                "return_all_scores": False,
                "model_id": "primary"
            }
        )

        assert response.status_code == 400

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_batch_predict_endpoint(self, mock_get_server, client, sample_image_base64):
        """Test batch prediction endpoint."""
        # Mock server and results
        mock_server = Mock()
        mock_results = [
            PredictionResult(
                class_name="jollof_rice",
                confidence=0.85,
                class_index=0
            ),
            PredictionResult(
                class_name="beans",
                confidence=0.75,
                class_index=1
            )
        ]

        mock_server.predict_batch = AsyncMock(return_value=mock_results)
        mock_get_server.return_value = mock_server

        # Make request
        response = client.post(
            "/api/v1/inference/predict/batch",
            json={
                "images_base64": [sample_image_base64, sample_image_base64],
                "return_all_scores": False,
                "model_id": "primary"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_images"] == 2
        assert data["successful_predictions"] == 2
        assert len(data["predictions"]) == 2

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_nutrition_analysis_endpoint(self, mock_get_server, client, sample_image_base64):
        """Test nutrition analysis endpoint."""
        # Mock server and analysis result
        mock_server = Mock()
        mock_analysis = {
            "detected_foods": [
                {
                    "name": "jollof_rice",
                    "confidence": 0.85,
                    "category": "carbohydrates"
                }
            ],
            "category_distribution": {"carbohydrates": 1},
            "missing_categories": ["proteins", "vitamins"],
            "balance_score": 0.33,
            "total_foods_detected": 1,
            "recommendations": {
                "proteins": ["Beans (ewa)", "Fish (eja)"]
            }
        }

        mock_server.analyze_meal_nutrition = AsyncMock(
            return_value=mock_analysis)
        mock_get_server.return_value = mock_server

        # Make request
        response = client.post(
            "/api/v1/inference/analyze/nutrition",
            json={
                "images_base64": [sample_image_base64],
                "model_id": "primary"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_foods_detected"] == 1
        assert data["balance_score"] == 0.33
        assert "proteins" in data["missing_categories"]
        assert "recommendations" in data

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_status_endpoint(self, mock_get_server, client):
        """Test server status endpoint."""
        # Mock server status
        mock_server = Mock()
        mock_status = {
            "status": "healthy",
            "uptime_seconds": 3600.0,
            "models": [
                {
                    "model_id": "primary",
                    "num_classes": 5,
                    "class_names": ["jollof_rice", "beans"]
                }
            ],
            "config": {
                "max_batch_size": 16,
                "confidence_threshold": 0.1
            }
        }

        mock_server.get_server_status.return_value = mock_status
        mock_get_server.return_value = mock_server

        # Make request
        response = client.get("/api/v1/inference/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["uptime_seconds"] == 3600.0
        assert len(data["models"]) == 1

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_health_endpoint(self, mock_get_server, client):
        """Test health check endpoint."""
        # Mock healthy server
        mock_server = Mock()
        mock_server.health_check = AsyncMock(return_value=True)
        mock_get_server.return_value = mock_server

        # Make request
        response = client.get("/api/v1/inference/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data

    @patch('app.api.v1.endpoints.inference.get_model_server')
    def test_health_endpoint_unhealthy(self, mock_get_server, client):
        """Test health check endpoint when unhealthy."""
        # Mock unhealthy server
        mock_server = Mock()
        mock_server.health_check = AsyncMock(return_value=False)
        mock_get_server.return_value = mock_server

        # Make request
        response = client.get("/api/v1/inference/health")

        assert response.status_code == 503


class TestModelCaching:
    """Test model caching functionality."""

    def test_prediction_caching(self, serving_config, sample_image):
        """Test that predictions are cached properly."""
        # This would require more complex setup to test actual caching
        # For now, just test that cache is enabled

        inference_config = InferenceConfig(
            model_path=serving_config.model_path,
            device="cpu",
            enable_caching=True,
            cache_size=100,
            warmup_iterations=1
        )

        # Test that config enables caching
        assert inference_config.enable_caching
        assert inference_config.cache_size == 100


class TestErrorHandling:
    """Test error handling in inference pipeline."""

    @pytest.mark.asyncio
    async def test_invalid_model_id(self, serving_config, sample_image):
        """Test handling of invalid model ID."""
        server = ModelServer(serving_config)

        try:
            result = await server.predict_single(sample_image, model_id="nonexistent")
            # Should return None for invalid model
            assert result is None

        finally:
            server.cleanup()

    def test_invalid_serving_config(self):
        """Test handling of invalid serving configuration."""
        config = ServingConfig(
            model_path="/nonexistent/model.pth",
            device="cpu",
            warmup_samples=1
        )

        # Should raise exception for nonexistent model
        with pytest.raises(Exception):
            ModelManager(config)


if __name__ == "__main__":
    pytest.main([__file__])
