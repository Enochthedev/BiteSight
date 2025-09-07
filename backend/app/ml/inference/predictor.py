"""
Production-optimized inference utilities for Nigerian food recognition.
Handles model loading, caching, and batch prediction with performance optimization.
"""

import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging
import time
from dataclasses import dataclass
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import hashlib

from ..models.mobilenet_food_classifier import MobileNetV2FoodClassifier, load_pretrained_model
from ..dataset.augmentation import get_inference_transforms
from ..dataset.food_mapping import NigerianFoodMapper
from ...core.cache_service import get_cache_service

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of food recognition prediction."""
    class_name: str
    confidence: float
    class_index: int
    nutritional_category: Optional[str] = None
    local_names: Optional[List[str]] = None


@dataclass
class InferenceConfig:
    """Configuration for inference."""
    model_path: str
    device: str = "auto"  # "auto", "cpu", "cuda"
    batch_size: int = 8
    confidence_threshold: float = 0.1
    top_k: int = 5
    enable_caching: bool = True
    cache_size: int = 1000
    num_threads: int = 4
    warmup_iterations: int = 5


class ModelCache:
    """Thread-safe cache for model predictions."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[any]:
        """Get item from cache."""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
        return None

    def put(self, key: str, value: any):
        """Put item in cache."""
        with self.lock:
            if key in self.cache:
                # Update existing item
                self.access_order.remove(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used item
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]

            self.cache[key] = value
            self.access_order.append(key)

    def clear(self):
        """Clear cache."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()


class FoodPredictor:
    """
    Production-optimized food recognition predictor.
    Handles model loading, preprocessing, and batch inference.
    """

    def __init__(self, config: InferenceConfig, food_mapper: Optional[NigerianFoodMapper] = None):
        """
        Initialize food predictor.

        Args:
            config: Inference configuration
            food_mapper: Food mapping utility for nutritional analysis
        """
        self.config = config
        self.food_mapper = food_mapper

        # Setup device
        if config.device == "auto":
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(config.device)

        # Load model
        self.model = None
        self.class_names = []
        self.transforms = None
        self.model_version = None
        self._load_model()

        # Setup cache (both local and Redis)
        self.cache = ModelCache(
            config.cache_size) if config.enable_caching else None
        self.redis_cache = get_cache_service()

        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=config.num_threads)

        # Warmup model
        self._warmup_model()

        logger.info(f"FoodPredictor initialized on device: {self.device}")

    def _load_model(self):
        """Load model and setup preprocessing."""
        try:
            # Load model checkpoint
            checkpoint = torch.load(
                self.config.model_path, map_location=self.device)

            # Extract model info
            if 'class_names' in checkpoint:
                self.class_names = checkpoint['class_names']
            else:
                # Fallback: generate class names
                num_classes = checkpoint['model_state_dict']['classifier.3.weight'].shape[0]
                self.class_names = [f"class_{i}" for i in range(num_classes)]

            # Generate model version for caching
            model_hash = hashlib.md5(str(checkpoint).encode()).hexdigest()[:8]
            self.model_version = f"mobilenet_v2_{model_hash}"

            # Create and load model
            self.model = MobileNetV2FoodClassifier(
                num_classes=len(self.class_names))

            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)

            self.model.to(self.device)
            self.model.eval()

            # Setup preprocessing
            self.transforms = get_inference_transforms()

            logger.info(
                f"Loaded model with {len(self.class_names)} classes, version: {self.model_version}")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def _warmup_model(self):
        """Warmup model with dummy inputs for consistent performance."""
        logger.info("Warming up model...")

        dummy_input = torch.randn(1, 3, 224, 224).to(self.device)

        with torch.no_grad():
            for _ in range(self.config.warmup_iterations):
                _ = self.model(dummy_input)

        logger.info("Model warmup completed")

    def _preprocess_image(self, image: Union[Image.Image, np.ndarray, str]) -> torch.Tensor:
        """
        Preprocess single image for inference.

        Args:
            image: PIL Image, numpy array, or path to image file

        Returns:
            Preprocessed tensor
        """
        if isinstance(image, str):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Apply transforms
        tensor = self.transforms(image)
        return tensor.unsqueeze(0)  # Add batch dimension

    def _preprocess_batch(self, images: List[Union[Image.Image, np.ndarray, str]]) -> torch.Tensor:
        """
        Preprocess batch of images for inference.

        Args:
            images: List of images

        Returns:
            Batched tensor
        """
        tensors = []
        for image in images:
            tensor = self._preprocess_image(image)
            tensors.append(tensor.squeeze(0))  # Remove batch dimension

        return torch.stack(tensors)

    def _create_cache_key(self, image_tensor: torch.Tensor) -> str:
        """Create cache key from image tensor."""
        # Use hash of tensor data for caching
        image_hash = hashlib.md5(
            image_tensor.cpu().numpy().tobytes()).hexdigest()
        return image_hash

    def predict_single(
        self,
        image: Union[Image.Image, np.ndarray, str],
        return_all_scores: bool = False
    ) -> Union[PredictionResult, List[PredictionResult]]:
        """
        Predict food class for single image.

        Args:
            image: Input image
            return_all_scores: Whether to return all top-k predictions

        Returns:
            Single prediction or list of top-k predictions
        """
        # Preprocess image
        image_tensor = self._preprocess_image(image).to(self.device)

        # Create cache key from image hash
        image_hash = hashlib.md5(
            image_tensor.cpu().numpy().tobytes()).hexdigest()

        # Check Redis cache first
        cached_result = self.redis_cache.get_cached_inference(
            image_hash, self.model_version)
        if cached_result is not None:
            logger.debug(f"Redis cache hit for image hash: {image_hash}")
            # Convert cached dict back to PredictionResult objects
            if return_all_scores and isinstance(cached_result, list):
                return [PredictionResult(**result) for result in cached_result]
            elif not return_all_scores and isinstance(cached_result, dict):
                return PredictionResult(**cached_result)
            elif cached_result is None:
                return None

        # Check local cache
        cache_key = None
        if self.cache:
            cache_key = image_hash
            local_cached_result = self.cache.get(cache_key)
            if local_cached_result is not None:
                logger.debug(f"Local cache hit for image hash: {image_hash}")
                return local_cached_result

        # Run inference
        with torch.no_grad():
            logits = self.model(image_tensor)
            probabilities = F.softmax(logits, dim=1)

            # Get top-k predictions
            top_probs, top_indices = torch.topk(
                probabilities, self.config.top_k, dim=1)
            top_probs = top_probs.squeeze().cpu().numpy()
            top_indices = top_indices.squeeze().cpu().numpy()

        # Create prediction results
        results = []
        for prob, idx in zip(top_probs, top_indices):
            if prob >= self.config.confidence_threshold:
                class_name = self.class_names[idx]

                # Get nutritional info if mapper available
                nutritional_category = None
                local_names = None
                if self.food_mapper:
                    food_info = self.food_mapper.get_food_class(class_name)
                    if food_info:
                        nutritional_category = food_info.nutritional_category.value
                        local_names = food_info.local_names

                result = PredictionResult(
                    class_name=class_name,
                    confidence=float(prob),
                    class_index=int(idx),
                    nutritional_category=nutritional_category,
                    local_names=local_names
                )
                results.append(result)

        # Prepare result for caching and return
        final_result = results if return_all_scores else (
            results[0] if results else None)

        # Cache result in Redis (convert to dict for JSON serialization)
        if final_result is not None:
            if return_all_scores:
                cache_data = [result.__dict__ for result in results]
            else:
                cache_data = final_result.__dict__
            self.redis_cache.cache_model_inference(
                image_hash, self.model_version, cache_data)

        # Cache result locally
        if self.cache and cache_key:
            self.cache.put(cache_key, final_result)

        return final_result

    def predict_batch(
        self,
        images: List[Union[Image.Image, np.ndarray, str]],
        return_all_scores: bool = False
    ) -> List[Union[PredictionResult, List[PredictionResult]]]:
        """
        Predict food classes for batch of images.

        Args:
            images: List of input images
            return_all_scores: Whether to return all top-k predictions for each image

        Returns:
            List of predictions for each image
        """
        if not images:
            return []

        # Process in batches
        all_results = []

        for i in range(0, len(images), self.config.batch_size):
            batch_images = images[i:i + self.config.batch_size]

            # Preprocess batch
            batch_tensor = self._preprocess_batch(batch_images).to(self.device)

            # Run inference
            with torch.no_grad():
                logits = self.model(batch_tensor)
                probabilities = F.softmax(logits, dim=1)

                # Get top-k predictions for each image in batch
                top_probs, top_indices = torch.topk(
                    probabilities, self.config.top_k, dim=1)
                top_probs = top_probs.cpu().numpy()
                top_indices = top_indices.cpu().numpy()

            # Process each image in batch
            for j in range(len(batch_images)):
                results = []

                for prob, idx in zip(top_probs[j], top_indices[j]):
                    if prob >= self.config.confidence_threshold:
                        class_name = self.class_names[idx]

                        # Get nutritional info if mapper available
                        nutritional_category = None
                        local_names = None
                        if self.food_mapper:
                            food_info = self.food_mapper.get_food_class(
                                class_name)
                            if food_info:
                                nutritional_category = food_info.nutritional_category.value
                                local_names = food_info.local_names

                        result = PredictionResult(
                            class_name=class_name,
                            confidence=float(prob),
                            class_index=int(idx),
                            nutritional_category=nutritional_category,
                            local_names=local_names
                        )
                        results.append(result)

                if return_all_scores:
                    all_results.append(results)
                else:
                    all_results.append(results[0] if results else None)

        return all_results

    def analyze_meal_nutrition(
        self,
        images: List[Union[Image.Image, np.ndarray, str]]
    ) -> Dict[str, any]:
        """
        Analyze nutritional content of a meal from multiple images.

        Args:
            images: List of meal images

        Returns:
            Nutritional analysis results
        """
        if not self.food_mapper:
            raise ValueError("Food mapper required for nutritional analysis")

        # Get predictions for all images
        predictions = self.predict_batch(images, return_all_scores=False)

        # Extract detected foods with confidence
        detected_foods = []
        for pred in predictions:
            if pred is not None:
                detected_foods.append((pred.class_name, pred.confidence))

        # Analyze nutrition using food mapper
        nutrition_analysis = self.food_mapper.analyze_meal_nutrition(
            detected_foods)

        # Add recommendations for missing categories
        if nutrition_analysis['missing_categories']:
            recommendations = self.food_mapper.get_recommendations_for_missing_categories(
                nutrition_analysis['missing_categories']
            )
            nutrition_analysis['recommendations'] = recommendations

        return nutrition_analysis

    def benchmark_performance(self, num_images: int = 100) -> Dict[str, float]:
        """
        Benchmark inference performance.

        Args:
            num_images: Number of dummy images to process

        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking performance with {num_images} images...")

        # Create dummy images
        dummy_images = [
            torch.randn(3, 224, 224) for _ in range(num_images)
        ]

        # Single image inference benchmark
        start_time = time.time()
        for img in dummy_images[:10]:  # Test with 10 images
            img_pil = Image.fromarray(
                (img.permute(1, 2, 0).numpy() * 255).astype(np.uint8))
            _ = self.predict_single(img_pil)
        single_time = (time.time() - start_time) / 10

        # Batch inference benchmark
        batch_images = [
            Image.fromarray(
                (img.permute(1, 2, 0).numpy() * 255).astype(np.uint8))
            for img in dummy_images
        ]

        start_time = time.time()
        _ = self.predict_batch(batch_images)
        batch_time = time.time() - start_time

        results = {
            'single_image_time': single_time,
            'batch_total_time': batch_time,
            'batch_per_image_time': batch_time / num_images,
            'batch_speedup': single_time / (batch_time / num_images),
            'throughput_fps': num_images / batch_time
        }

        logger.info(f"Performance results: {results}")
        return results

    def get_model_info(self) -> Dict[str, any]:
        """Get model information."""
        return {
            'model_type': 'MobileNetV2FoodClassifier',
            'num_classes': len(self.class_names),
            'class_names': self.class_names,
            'device': str(self.device),
            'model_parameters': sum(p.numel() for p in self.model.parameters()),
            'config': self.config
        }

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)

        if self.cache:
            self.cache.clear()


def create_predictor(
    model_path: str,
    food_mapper: Optional[NigerianFoodMapper] = None,
    config: Optional[InferenceConfig] = None
) -> FoodPredictor:
    """
    Factory function to create a food predictor.

    Args:
        model_path: Path to trained model
        food_mapper: Food mapping utility
        config: Inference configuration

    Returns:
        Initialized predictor
    """
    if config is None:
        config = InferenceConfig(model_path=model_path)
    else:
        config.model_path = model_path

    return FoodPredictor(config=config, food_mapper=food_mapper)


def load_predictor_from_checkpoint(
    checkpoint_dir: str,
    food_mapper: Optional[NigerianFoodMapper] = None,
    use_best: bool = True
) -> FoodPredictor:
    """
    Load predictor from training checkpoint directory.

    Args:
        checkpoint_dir: Directory containing model checkpoints
        food_mapper: Food mapping utility
        use_best: Whether to use best model or latest checkpoint

    Returns:
        Loaded predictor
    """
    checkpoint_path = Path(checkpoint_dir)

    if use_best:
        model_file = checkpoint_path / "best_model.pth"
    else:
        # Find latest checkpoint
        checkpoints = list(checkpoint_path.glob("checkpoint_epoch_*.pth"))
        if not checkpoints:
            raise FileNotFoundError(
                f"No checkpoints found in {checkpoint_dir}")

        # Sort by epoch number
        checkpoints.sort(key=lambda x: int(x.stem.split('_')[-1]))
        model_file = checkpoints[-1]

    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")

    config = InferenceConfig(model_path=str(model_file))
    return FoodPredictor(config=config, food_mapper=food_mapper)
