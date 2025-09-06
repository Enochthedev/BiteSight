"""
Tests for ML model components.
Tests model architecture, training pipeline, and inference utilities.
"""

import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image
import json

from app.ml.models.mobilenet_food_classifier import (
    MobileNetV2FoodClassifier, FoodClassificationHead, EnsembleFoodClassifier,
    create_mobilenet_food_classifier, count_parameters
)
from app.ml.training.trainer import (
    FoodModelTrainer, TrainingConfig, TrainingMetrics, create_trainer
)
from app.ml.inference.predictor import (
    FoodPredictor, InferenceConfig, PredictionResult, ModelCache,
    create_predictor
)
from app.ml.dataset.food_mapping import NigerianFoodMapper


class TestMobileNetV2FoodClassifier:
    """Test cases for MobileNetV2 food classifier."""

    @pytest.fixture
    def sample_model(self):
        """Create sample model for testing."""
        return MobileNetV2FoodClassifier(num_classes=10, pretrained=False)

    def test_model_initialization(self, sample_model):
        """Test model initialization."""
        assert sample_model.num_classes == 10
        assert isinstance(sample_model.backbone, nn.Module)
        assert isinstance(sample_model.classifier, nn.Sequential)

    def test_forward_pass(self, sample_model):
        """Test forward pass through model."""
        batch_size = 4
        input_tensor = torch.randn(batch_size, 3, 224, 224)

        output = sample_model(input_tensor)

        assert output.shape == (batch_size, 10)
        assert not torch.isnan(output).any()

    def test_feature_extraction(self, sample_model):
        """Test feature extraction."""
        input_tensor = torch.randn(2, 3, 224, 224)

        features = sample_model.extract_features(input_tensor)

        assert features.shape == (2, sample_model.feature_dim)
        assert not torch.isnan(features).any()

    def test_predict_proba(self, sample_model):
        """Test probability prediction."""
        input_tensor = torch.randn(3, 3, 224, 224)

        probs = sample_model.predict_proba(input_tensor)

        assert probs.shape == (3, 10)
        assert torch.allclose(probs.sum(dim=1), torch.ones(3), atol=1e-6)
        assert (probs >= 0).all() and (probs <= 1).all()

    def test_predict_top_k(self, sample_model):
        """Test top-k prediction."""
        input_tensor = torch.randn(2, 3, 224, 224)
        k = 3

        top_probs, top_indices = sample_model.predict_top_k(input_tensor, k=k)

        assert top_probs.shape == (2, k)
        assert top_indices.shape == (2, k)
        assert (top_indices >= 0).all() and (top_indices < 10).all()

    def test_freeze_unfreeze_backbone(self, sample_model):
        """Test freezing and unfreezing backbone."""
        # Initially all parameters should be trainable
        assert all(p.requires_grad for p in sample_model.backbone.parameters())

        # Freeze backbone
        sample_model.freeze_backbone()
        assert not any(
            p.requires_grad for p in sample_model.backbone.parameters())

        # Unfreeze backbone
        sample_model.unfreeze_backbone()
        assert all(p.requires_grad for p in sample_model.backbone.parameters())

    def test_get_model_info(self, sample_model):
        """Test model info retrieval."""
        info = sample_model.get_model_info()

        assert 'model_name' in info
        assert 'num_classes' in info
        assert 'total_parameters' in info
        assert 'trainable_parameters' in info
        assert info['num_classes'] == 10

    def test_create_mobilenet_food_classifier(self):
        """Test factory function."""
        model = create_mobilenet_food_classifier(
            num_classes=15, pretrained=False)

        assert isinstance(model, MobileNetV2FoodClassifier)
        assert model.num_classes == 15

    def test_count_parameters(self, sample_model):
        """Test parameter counting utility."""
        total_params, trainable_params = count_parameters(sample_model)

        assert isinstance(total_params, int)
        assert isinstance(trainable_params, int)
        assert total_params >= trainable_params
        assert total_params > 0


class TestFoodClassificationHead:
    """Test cases for custom classification head."""

    def test_classification_head_init(self):
        """Test classification head initialization."""
        head = FoodClassificationHead(
            input_dim=1280,
            num_classes=10,
            hidden_dims=[512, 256],
            dropout_rate=0.2
        )

        assert isinstance(head.classifier, nn.Sequential)

    def test_classification_head_forward(self):
        """Test forward pass through classification head."""
        head = FoodClassificationHead(
            input_dim=1280,
            num_classes=10,
            hidden_dims=[512]
        )

        input_tensor = torch.randn(4, 1280)
        output = head(input_tensor)

        assert output.shape == (4, 10)


class TestEnsembleFoodClassifier:
    """Test cases for ensemble classifier."""

    @pytest.fixture
    def sample_models(self):
        """Create sample models for ensemble."""
        models = [
            MobileNetV2FoodClassifier(num_classes=5, pretrained=False)
            for _ in range(3)
        ]
        return models

    def test_ensemble_init(self, sample_models):
        """Test ensemble initialization."""
        ensemble = EnsembleFoodClassifier(sample_models)

        assert len(ensemble.models) == 3
        assert ensemble.num_classes == 5

    def test_ensemble_forward(self, sample_models):
        """Test ensemble forward pass."""
        ensemble = EnsembleFoodClassifier(sample_models)
        input_tensor = torch.randn(2, 3, 224, 224)

        output = ensemble(input_tensor)

        assert output.shape == (2, 5)

    def test_ensemble_predict_proba(self, sample_models):
        """Test ensemble probability prediction."""
        ensemble = EnsembleFoodClassifier(sample_models)
        input_tensor = torch.randn(2, 3, 224, 224)

        probs = ensemble.predict_proba(input_tensor)

        assert probs.shape == (2, 5)
        assert torch.allclose(probs.sum(dim=1), torch.ones(2), atol=1e-6)


class TestTrainingPipeline:
    """Test cases for training pipeline."""

    @pytest.fixture
    def sample_data(self):
        """Create sample training data."""
        # Create dummy dataset
        num_samples = 100
        images = torch.randn(num_samples, 3, 224, 224)
        labels = torch.randint(0, 5, (num_samples,))

        dataset = TensorDataset(images, labels)
        train_loader = DataLoader(dataset, batch_size=8, shuffle=True)
        val_loader = DataLoader(dataset, batch_size=8, shuffle=False)

        return train_loader, val_loader

    @pytest.fixture
    def sample_config(self):
        """Create sample training configuration."""
        return TrainingConfig(
            epochs=2,
            learning_rate=0.01,
            batch_size=8,
            early_stopping_patience=5,
            mixed_precision=False  # Disable for testing
        )

    def test_training_config(self, sample_config):
        """Test training configuration."""
        assert sample_config.epochs == 2
        assert sample_config.learning_rate == 0.01
        assert sample_config.batch_size == 8

    def test_training_metrics(self):
        """Test training metrics dataclass."""
        metrics = TrainingMetrics(
            epoch=1,
            train_loss=0.5,
            train_accuracy=85.0,
            val_loss=0.6,
            val_accuracy=80.0,
            learning_rate=0.001,
            epoch_time=30.0
        )

        assert metrics.epoch == 1
        assert metrics.train_accuracy == 85.0

    def test_trainer_initialization(self, sample_data, sample_config):
        """Test trainer initialization."""
        train_loader, val_loader = sample_data
        model = MobileNetV2FoodClassifier(num_classes=5, pretrained=False)

        trainer = FoodModelTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            config=sample_config
        )

        assert trainer.model == model
        assert trainer.config == sample_config
        assert isinstance(trainer.optimizer, torch.optim.SGD)
        assert isinstance(trainer.criterion, nn.CrossEntropyLoss)

    def test_create_trainer_factory(self, sample_data):
        """Test trainer factory function."""
        train_loader, val_loader = sample_data
        model = MobileNetV2FoodClassifier(num_classes=5, pretrained=False)

        trainer = create_trainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader
        )

        assert isinstance(trainer, FoodModelTrainer)

    def test_train_epoch(self, sample_data, sample_config):
        """Test single epoch training."""
        train_loader, val_loader = sample_data
        model = MobileNetV2FoodClassifier(num_classes=5, pretrained=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            sample_config.checkpoint_dir = temp_dir
            sample_config.log_dir = temp_dir

            trainer = FoodModelTrainer(
                model=model,
                train_loader=train_loader,
                val_loader=val_loader,
                config=sample_config
            )

            train_loss, train_accuracy = trainer.train_epoch()

            assert isinstance(train_loss, float)
            assert isinstance(train_accuracy, float)
            assert train_loss >= 0
            assert 0 <= train_accuracy <= 100

    def test_validate_epoch(self, sample_data, sample_config):
        """Test single epoch validation."""
        train_loader, val_loader = sample_data
        model = MobileNetV2FoodClassifier(num_classes=5, pretrained=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            sample_config.checkpoint_dir = temp_dir
            sample_config.log_dir = temp_dir

            trainer = FoodModelTrainer(
                model=model,
                train_loader=train_loader,
                val_loader=val_loader,
                config=sample_config
            )

            val_loss, val_accuracy = trainer.validate_epoch()

            assert isinstance(val_loss, float)
            assert isinstance(val_accuracy, float)
            assert val_loss >= 0
            assert 0 <= val_accuracy <= 100


class TestModelCache:
    """Test cases for model cache."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = ModelCache(max_size=10)

        assert cache.max_size == 10
        assert len(cache.cache) == 0

    def test_cache_put_get(self):
        """Test cache put and get operations."""
        cache = ModelCache(max_size=3)

        # Put items
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Get items
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("nonexistent") is None

    def test_cache_eviction(self):
        """Test cache eviction when full."""
        cache = ModelCache(max_size=2)

        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Add third item (should evict first)
        cache.put("key3", "value3")

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = ModelCache(max_size=5)

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        cache.clear()

        assert len(cache.cache) == 0
        assert cache.get("key1") is None


class TestInferencePredictor:
    """Test cases for inference predictor."""

    @pytest.fixture
    def sample_model_checkpoint(self):
        """Create sample model checkpoint for testing."""
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as f:
            model = MobileNetV2FoodClassifier(num_classes=5, pretrained=False)

            checkpoint = {
                'model_state_dict': model.state_dict(),
                'class_names': ['class_0', 'class_1', 'class_2', 'class_3', 'class_4']
            }

            torch.save(checkpoint, f.name)
            yield f.name

            # Cleanup
            Path(f.name).unlink()

    @pytest.fixture
    def sample_image(self):
        """Create sample PIL image for testing."""
        return Image.new('RGB', (224, 224), color='blue')

    def test_inference_config(self):
        """Test inference configuration."""
        config = InferenceConfig(
            model_path="test_model.pth",
            batch_size=16,
            confidence_threshold=0.5
        )

        assert config.model_path == "test_model.pth"
        assert config.batch_size == 16
        assert config.confidence_threshold == 0.5

    def test_prediction_result(self):
        """Test prediction result dataclass."""
        result = PredictionResult(
            class_name="jollof_rice",
            confidence=0.85,
            class_index=0,
            nutritional_category="carbohydrates"
        )

        assert result.class_name == "jollof_rice"
        assert result.confidence == 0.85
        assert result.nutritional_category == "carbohydrates"

    def test_predictor_initialization(self, sample_model_checkpoint):
        """Test predictor initialization."""
        config = InferenceConfig(
            model_path=sample_model_checkpoint,
            device="cpu",
            warmup_iterations=1
        )

        predictor = FoodPredictor(config=config)

        assert predictor.model is not None
        assert len(predictor.class_names) == 5
        assert predictor.device.type == "cpu"

    def test_create_predictor_factory(self, sample_model_checkpoint):
        """Test predictor factory function."""
        predictor = create_predictor(
            model_path=sample_model_checkpoint,
            config=InferenceConfig(
                model_path=sample_model_checkpoint,
                device="cpu",
                warmup_iterations=1
            )
        )

        assert isinstance(predictor, FoodPredictor)

    def test_preprocess_image(self, sample_model_checkpoint, sample_image):
        """Test image preprocessing."""
        config = InferenceConfig(
            model_path=sample_model_checkpoint,
            device="cpu",
            warmup_iterations=1
        )
        predictor = FoodPredictor(config=config)

        tensor = predictor._preprocess_image(sample_image)

        assert tensor.shape == (1, 3, 224, 224)
        assert tensor.dtype == torch.float32

    def test_predict_single(self, sample_model_checkpoint, sample_image):
        """Test single image prediction."""
        config = InferenceConfig(
            model_path=sample_model_checkpoint,
            device="cpu",
            confidence_threshold=0.0,  # Accept all predictions for testing
            warmup_iterations=1
        )
        predictor = FoodPredictor(config=config)

        result = predictor.predict_single(sample_image)

        assert result is not None
        assert isinstance(result, PredictionResult)
        assert result.class_name in predictor.class_names
        assert 0 <= result.confidence <= 1

    def test_predict_batch(self, sample_model_checkpoint, sample_image):
        """Test batch prediction."""
        config = InferenceConfig(
            model_path=sample_model_checkpoint,
            device="cpu",
            confidence_threshold=0.0,
            batch_size=2,
            warmup_iterations=1
        )
        predictor = FoodPredictor(config=config)

        images = [sample_image, sample_image, sample_image]
        results = predictor.predict_batch(images)

        assert len(results) == 3
        for result in results:
            assert result is not None
            assert isinstance(result, PredictionResult)

    def test_get_model_info(self, sample_model_checkpoint):
        """Test model info retrieval."""
        config = InferenceConfig(
            model_path=sample_model_checkpoint,
            device="cpu",
            warmup_iterations=1
        )
        predictor = FoodPredictor(config=config)

        info = predictor.get_model_info()

        assert 'model_type' in info
        assert 'num_classes' in info
        assert 'class_names' in info
        assert info['num_classes'] == 5


if __name__ == "__main__":
    pytest.main([__file__])
