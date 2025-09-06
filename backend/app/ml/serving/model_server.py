"""
Model serving infrastructure for Nigerian food recognition.
Handles model loading, caching, and serving with proper error handling.
"""

import torch
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
import time
from dataclasses import dataclass, asdict
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

from ..inference.predictor import FoodPredictor, InferenceConfig, PredictionResult
from ..dataset.food_mapping import NigerianFoodMapper

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a loaded model."""
    model_id: str
    model_path: str
    num_classes: int
    class_names: List[str]
    loaded_at: float
    last_used: float
    prediction_count: int
    average_inference_time: float


@dataclass
class ServingConfig:
    """Configuration for model serving."""
    model_path: str
    food_mapping_path: Optional[str] = None
    device: str = "auto"
    max_batch_size: int = 16
    model_cache_size: int = 2
    prediction_cache_size: int = 1000
    cache_ttl: int = 3600  # seconds
    warmup_samples: int = 5
    confidence_threshold: float = 0.1
    enable_batch_processing: bool = True
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    health_check_interval: float = 60.0


class ModelManager:
    """
    Manages multiple models with caching and lifecycle management.
    """

    def __init__(self, config: ServingConfig):
        self.config = config
        self.models: Dict[str, FoodPredictor] = {}
        self.model_info: Dict[str, ModelInfo] = {}
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(
            max_workers=config.max_concurrent_requests)

        # Load food mapper if provided
        self.food_mapper = None
        if config.food_mapping_path:
            self.food_mapper = NigerianFoodMapper(
                Path(config.food_mapping_path))

        # Load primary model
        self._load_primary_model()

        logger.info("ModelManager initialized")

    def _load_primary_model(self):
        """Load the primary model."""
        model_id = "primary"

        try:
            inference_config = InferenceConfig(
                model_path=self.config.model_path,
                device=self.config.device,
                batch_size=self.config.max_batch_size,
                confidence_threshold=self.config.confidence_threshold,
                enable_caching=True,
                cache_size=self.config.prediction_cache_size,
                warmup_iterations=self.config.warmup_samples
            )

            predictor = FoodPredictor(
                config=inference_config,
                food_mapper=self.food_mapper
            )

            # Store model and info
            with self.lock:
                self.models[model_id] = predictor

                model_info_dict = predictor.get_model_info()
                self.model_info[model_id] = ModelInfo(
                    model_id=model_id,
                    model_path=self.config.model_path,
                    num_classes=model_info_dict['num_classes'],
                    class_names=model_info_dict['class_names'],
                    loaded_at=time.time(),
                    last_used=time.time(),
                    prediction_count=0,
                    average_inference_time=0.0
                )

            logger.info(f"Loaded primary model: {model_id}")

        except Exception as e:
            logger.error(f"Failed to load primary model: {e}")
            raise

    def get_model(self, model_id: str = "primary") -> Optional[FoodPredictor]:
        """Get model by ID."""
        with self.lock:
            if model_id in self.models:
                self.model_info[model_id].last_used = time.time()
                return self.models[model_id]
        return None

    def get_model_info(self, model_id: str = "primary") -> Optional[ModelInfo]:
        """Get model information."""
        with self.lock:
            return self.model_info.get(model_id)

    def list_models(self) -> List[ModelInfo]:
        """List all loaded models."""
        with self.lock:
            return list(self.model_info.values())

    def update_model_stats(self, model_id: str, inference_time: float):
        """Update model usage statistics."""
        with self.lock:
            if model_id in self.model_info:
                info = self.model_info[model_id]
                info.prediction_count += 1

                # Update average inference time
                if info.average_inference_time == 0:
                    info.average_inference_time = inference_time
                else:
                    # Exponential moving average
                    alpha = 0.1
                    info.average_inference_time = (
                        alpha * inference_time +
                        (1 - alpha) * info.average_inference_time
                    )

    def cleanup(self):
        """Cleanup resources."""
        with self.lock:
            for predictor in self.models.values():
                predictor.cleanup()
            self.models.clear()
            self.model_info.clear()

        self.executor.shutdown(wait=True)


class ModelServer:
    """
    High-level model server with request handling and error management.
    """

    def __init__(self, config: ServingConfig):
        self.config = config
        self.model_manager = ModelManager(config)
        self.request_semaphore = asyncio.Semaphore(
            config.max_concurrent_requests)
        self.is_healthy = True
        self.start_time = time.time()

        logger.info("ModelServer initialized")

    async def predict_single(
        self,
        image_data: Any,
        model_id: str = "primary",
        return_all_scores: bool = False
    ) -> Union[PredictionResult, List[PredictionResult], None]:
        """
        Predict food class for single image.

        Args:
            image_data: Image data (PIL Image, numpy array, or file path)
            model_id: Model identifier
            return_all_scores: Whether to return all top-k predictions

        Returns:
            Prediction result(s) or None if failed
        """
        async with self.request_semaphore:
            try:
                start_time = time.time()

                # Get model
                model = self.model_manager.get_model(model_id)
                if model is None:
                    raise ValueError(f"Model not found: {model_id}")

                # Run prediction in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.model_manager.executor,
                    lambda: model.predict_single(image_data, return_all_scores)
                )

                # Update stats
                inference_time = time.time() - start_time
                self.model_manager.update_model_stats(model_id, inference_time)

                return result

            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                return None

    async def predict_batch(
        self,
        images_data: List[Any],
        model_id: str = "primary",
        return_all_scores: bool = False
    ) -> List[Union[PredictionResult, List[PredictionResult], None]]:
        """
        Predict food classes for batch of images.

        Args:
            images_data: List of image data
            model_id: Model identifier
            return_all_scores: Whether to return all top-k predictions

        Returns:
            List of prediction results
        """
        if not self.config.enable_batch_processing:
            # Process individually
            tasks = [
                self.predict_single(img, model_id, return_all_scores)
                for img in images_data
            ]
            return await asyncio.gather(*tasks)

        async with self.request_semaphore:
            try:
                start_time = time.time()

                # Get model
                model = self.model_manager.get_model(model_id)
                if model is None:
                    raise ValueError(f"Model not found: {model_id}")

                # Run batch prediction in thread pool
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    self.model_manager.executor,
                    lambda: model.predict_batch(images_data, return_all_scores)
                )

                # Update stats
                inference_time = time.time() - start_time
                self.model_manager.update_model_stats(model_id, inference_time)

                return results

            except Exception as e:
                logger.error(f"Batch prediction failed: {e}")
                return [None] * len(images_data)

    async def analyze_meal_nutrition(
        self,
        images_data: List[Any],
        model_id: str = "primary"
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze nutritional content of a meal from multiple images.

        Args:
            images_data: List of meal images
            model_id: Model identifier

        Returns:
            Nutritional analysis results or None if failed
        """
        async with self.request_semaphore:
            try:
                start_time = time.time()

                # Get model
                model = self.model_manager.get_model(model_id)
                if model is None:
                    raise ValueError(f"Model not found: {model_id}")

                # Run analysis in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.model_manager.executor,
                    lambda: model.analyze_meal_nutrition(images_data)
                )

                # Update stats
                inference_time = time.time() - start_time
                self.model_manager.update_model_stats(model_id, inference_time)

                return result

            except Exception as e:
                logger.error(f"Meal analysis failed: {e}")
                return None

    def get_server_status(self) -> Dict[str, Any]:
        """Get server status and statistics."""
        uptime = time.time() - self.start_time
        models_info = [asdict(info)
                       for info in self.model_manager.list_models()]

        return {
            "status": "healthy" if self.is_healthy else "unhealthy",
            "uptime_seconds": uptime,
            "models": models_info,
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_concurrent_requests": self.config.max_concurrent_requests,
                "confidence_threshold": self.config.confidence_threshold,
                "enable_batch_processing": self.config.enable_batch_processing
            }
        }

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            # Check if primary model is available
            model = self.model_manager.get_model("primary")
            if model is None:
                self.is_healthy = False
                return False

            # Try a simple prediction with dummy data
            import numpy as np
            from PIL import Image

            dummy_image = Image.fromarray(
                (np.random.rand(224, 224, 3) * 255).astype(np.uint8)
            )

            result = await self.predict_single(dummy_image)
            self.is_healthy = result is not None

            return self.is_healthy

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.is_healthy = False
            return False

    def cleanup(self):
        """Cleanup server resources."""
        self.model_manager.cleanup()


# Global server instance
_server_instance: Optional[ModelServer] = None
_server_lock = threading.Lock()


def get_server_instance(config: Optional[ServingConfig] = None) -> ModelServer:
    """
    Get or create global server instance.

    Args:
        config: Server configuration (required for first call)

    Returns:
        ModelServer instance
    """
    global _server_instance

    with _server_lock:
        if _server_instance is None:
            if config is None:
                raise ValueError(
                    "Config required for first server initialization")
            _server_instance = ModelServer(config)

        return _server_instance


def cleanup_server():
    """Cleanup global server instance."""
    global _server_instance

    with _server_lock:
        if _server_instance is not None:
            _server_instance.cleanup()
            _server_instance = None


@asynccontextmanager
async def model_server_context(config: ServingConfig):
    """
    Async context manager for model server lifecycle.

    Args:
        config: Server configuration

    Yields:
        ModelServer instance
    """
    server = ModelServer(config)
    try:
        yield server
    finally:
        server.cleanup()


# Utility functions for common operations
async def quick_predict(
    image_data: Any,
    model_path: str,
    food_mapping_path: Optional[str] = None,
    confidence_threshold: float = 0.1
) -> Optional[PredictionResult]:
    """
    Quick prediction utility for single images.

    Args:
        image_data: Image data
        model_path: Path to model file
        food_mapping_path: Path to food mapping file
        confidence_threshold: Minimum confidence threshold

    Returns:
        Prediction result or None
    """
    config = ServingConfig(
        model_path=model_path,
        food_mapping_path=food_mapping_path,
        confidence_threshold=confidence_threshold,
        warmup_samples=1
    )

    async with model_server_context(config) as server:
        return await server.predict_single(image_data)


async def quick_meal_analysis(
    images_data: List[Any],
    model_path: str,
    food_mapping_path: str,
    confidence_threshold: float = 0.1
) -> Optional[Dict[str, Any]]:
    """
    Quick meal analysis utility.

    Args:
        images_data: List of meal images
        model_path: Path to model file
        food_mapping_path: Path to food mapping file
        confidence_threshold: Minimum confidence threshold

    Returns:
        Nutritional analysis or None
    """
    config = ServingConfig(
        model_path=model_path,
        food_mapping_path=food_mapping_path,
        confidence_threshold=confidence_threshold,
        warmup_samples=1
    )

    async with model_server_context(config) as server:
        return await server.analyze_meal_nutrition(images_data)
