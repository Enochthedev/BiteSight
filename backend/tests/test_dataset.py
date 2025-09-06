"""
Tests for dataset preprocessing functions.
Tests data loading, augmentation, validation, and food mapping utilities.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
from PIL import Image
import torch

from app.ml.dataset.data_loader import NigerianFoodDataset, DatasetLoader, FoodItem
from app.ml.dataset.augmentation import (
    FoodAugmentation, FoodSpecificTransform, AugmentationConfig,
    get_training_transforms, get_validation_transforms
)
from app.ml.dataset.validation import (
    ImageQualityChecker, DatasetValidator, ImageQualityMetrics
)
from app.ml.dataset.food_mapping import (
    NigerianFoodMapper, NutritionalCategory, FoodClassInfo, create_sample_metadata_file
)


class TestDataLoader:
    """Test cases for data loading utilities."""

    @pytest.fixture
    def temp_dataset_dir(self):
        """Create temporary dataset directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            for split in ['train', 'val', 'test']:
                (temp_path / 'images' / split).mkdir(parents=True)
            (temp_path / 'metadata').mkdir()

            # Create sample metadata
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

            with open(temp_path / 'metadata' / 'nigerian_foods.json', 'w') as f:
                json.dump(metadata, f)

            # Create sample images
            for split in ['train', 'val', 'test']:
                for food in ['jollof_rice', 'beans']:
                    food_dir = temp_path / 'images' / split / food
                    food_dir.mkdir()

                    # Create dummy image
                    img = Image.new('RGB', (224, 224), color='red')
                    img.save(food_dir / 'sample.jpg')

            yield temp_path

    def test_food_item_creation(self):
        """Test FoodItem dataclass creation."""
        food_item = FoodItem(
            name="jollof_rice",
            local_names=["jollof", "party rice"],
            food_class="jollof_rice",
            image_paths=["/path/to/image.jpg"],
            nutritional_category="carbohydrates"
        )

        assert food_item.name == "jollof_rice"
        assert "jollof" in food_item.local_names
        assert food_item.nutritional_category == "carbohydrates"

    def test_nigerian_food_dataset_init(self, temp_dataset_dir):
        """Test NigerianFoodDataset initialization."""
        dataset = NigerianFoodDataset(temp_dataset_dir, split="train")

        assert len(dataset.food_items) == 2
        assert "jollof_rice" in dataset.food_items
        assert "beans" in dataset.food_items
        assert len(dataset.class_to_idx) == 2
        assert len(dataset.samples) > 0

    def test_dataset_getitem(self, temp_dataset_dir):
        """Test dataset __getitem__ method."""
        dataset = NigerianFoodDataset(temp_dataset_dir, split="train")

        if len(dataset) > 0:
            image, target = dataset[0]
            assert isinstance(image, Image.Image)
            assert isinstance(target, int)
            assert 0 <= target < len(dataset.class_to_idx)

    def test_dataset_loader_validation(self, temp_dataset_dir):
        """Test DatasetLoader validation."""
        loader = DatasetLoader(temp_dataset_dir)

        # Should not raise exception for valid structure
        assert loader.data_dir == temp_dataset_dir

    def test_dataset_loader_invalid_structure(self):
        """Test DatasetLoader with invalid structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileNotFoundError):
                DatasetLoader(temp_dir)

    def test_create_dataloaders(self, temp_dataset_dir):
        """Test dataloader creation."""
        loader = DatasetLoader(temp_dataset_dir)
        train_loader, val_loader, test_loader = loader.create_dataloaders(
            batch_size=2)

        assert train_loader.batch_size == 2
        assert val_loader.batch_size == 2
        assert test_loader.batch_size == 2

    def test_dataset_statistics(self, temp_dataset_dir):
        """Test dataset statistics generation."""
        loader = DatasetLoader(temp_dataset_dir)
        stats = loader.get_dataset_statistics()

        assert 'train' in stats
        assert 'val' in stats
        assert 'test' in stats

        for split_stats in stats.values():
            assert 'num_samples' in split_stats
            assert 'num_classes' in split_stats
            assert 'class_names' in split_stats


class TestAugmentation:
    """Test cases for image augmentation."""

    @pytest.fixture
    def sample_image(self):
        """Create sample PIL image for testing."""
        return Image.new('RGB', (224, 224), color='blue')

    def test_random_lighting(self, sample_image):
        """Test random lighting augmentation."""
        augmented = FoodAugmentation.random_lighting(sample_image)
        assert isinstance(augmented, Image.Image)
        assert augmented.size == sample_image.size

    def test_random_contrast(self, sample_image):
        """Test random contrast augmentation."""
        augmented = FoodAugmentation.random_contrast(sample_image)
        assert isinstance(augmented, Image.Image)
        assert augmented.size == sample_image.size

    def test_random_saturation(self, sample_image):
        """Test random saturation augmentation."""
        augmented = FoodAugmentation.random_saturation(sample_image)
        assert isinstance(augmented, Image.Image)
        assert augmented.size == sample_image.size

    def test_random_blur(self, sample_image):
        """Test random blur augmentation."""
        # Test with high probability to ensure blur is applied
        augmented = FoodAugmentation.random_blur(
            sample_image, blur_probability=1.0)
        assert isinstance(augmented, Image.Image)
        assert augmented.size == sample_image.size

    def test_random_noise(self, sample_image):
        """Test random noise augmentation."""
        # Test with high probability to ensure noise is applied
        augmented = FoodAugmentation.random_noise(
            sample_image, noise_probability=1.0)
        assert isinstance(augmented, Image.Image)
        assert augmented.size == sample_image.size

    def test_food_specific_transform(self, sample_image):
        """Test FoodSpecificTransform."""
        transform = FoodSpecificTransform()
        augmented = transform(sample_image)
        assert isinstance(augmented, Image.Image)
        assert augmented.size == sample_image.size

    def test_training_transforms(self):
        """Test training transform pipeline."""
        transforms = get_training_transforms()

        # Create sample tensor input
        sample_image = Image.new('RGB', (256, 256), color='green')
        result = transforms(sample_image)

        assert isinstance(result, torch.Tensor)
        assert result.shape == (3, 224, 224)  # C, H, W

    def test_validation_transforms(self):
        """Test validation transform pipeline."""
        transforms = get_validation_transforms()

        sample_image = Image.new('RGB', (256, 256), color='green')
        result = transforms(sample_image)

        assert isinstance(result, torch.Tensor)
        assert result.shape == (3, 224, 224)

    def test_augmentation_config(self):
        """Test AugmentationConfig class."""
        config = AugmentationConfig(
            input_size=256,
            horizontal_flip_prob=0.3,
            rotation_degrees=10
        )

        train_transforms = config.get_training_transforms()
        val_transforms = config.get_validation_transforms()

        assert train_transforms is not None
        assert val_transforms is not None


class TestValidation:
    """Test cases for dataset validation."""

    @pytest.fixture
    def sample_image_path(self):
        """Create temporary image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (300, 300), color='red')
            img.save(f.name)
            yield Path(f.name)
            Path(f.name).unlink()

    def test_image_quality_checker_init(self):
        """Test ImageQualityChecker initialization."""
        checker = ImageQualityChecker()
        assert checker.min_resolution == (224, 224)
        assert checker.max_file_size_mb == 10.0

    def test_check_image_quality(self, sample_image_path):
        """Test image quality checking."""
        checker = ImageQualityChecker()
        metrics = checker.check_image_quality(sample_image_path)

        assert isinstance(metrics, ImageQualityMetrics)
        assert metrics.width == 300
        assert metrics.height == 300
        assert metrics.channels == 3
        assert not metrics.is_corrupted
        assert 0 <= metrics.brightness_mean <= 1
        assert metrics.aspect_ratio == 1.0

    def test_quality_acceptance(self, sample_image_path):
        """Test quality acceptance criteria."""
        checker = ImageQualityChecker()
        metrics = checker.check_image_quality(sample_image_path)
        is_acceptable, issues = checker.is_quality_acceptable(metrics)

        assert isinstance(is_acceptable, bool)
        assert isinstance(issues, list)

    def test_corrupted_image_handling(self):
        """Test handling of corrupted images."""
        checker = ImageQualityChecker()

        # Test with non-existent file
        fake_path = Path("/non/existent/file.jpg")
        metrics = checker.check_image_quality(fake_path)

        assert metrics.is_corrupted
        assert metrics.width == 0
        assert metrics.height == 0

    def test_dataset_validator_init(self):
        """Test DatasetValidator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create minimal structure
            for split in ['train', 'val', 'test']:
                (temp_path / 'images' / split).mkdir(parents=True)
            (temp_path / 'metadata').mkdir()

            # Create metadata file
            with open(temp_path / 'metadata' / 'nigerian_foods.json', 'w') as f:
                json.dump({"foods": []}, f)

            validator = DatasetValidator(temp_path)
            assert validator.dataset_root == temp_path

    def test_validate_dataset_structure(self):
        """Test dataset structure validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            validator = DatasetValidator(temp_path)

            is_valid, issues = validator.validate_dataset_structure()
            assert not is_valid
            assert len(issues) > 0

    def test_validate_metadata(self):
        """Test metadata validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / 'metadata').mkdir()

            # Create invalid metadata
            with open(temp_path / 'metadata' / 'nigerian_foods.json', 'w') as f:
                json.dump({"invalid": "structure"}, f)

            validator = DatasetValidator(temp_path)
            is_valid, issues = validator.validate_metadata()

            assert not is_valid
            assert len(issues) > 0


class TestFoodMapping:
    """Test cases for food mapping utilities."""

    def test_nutritional_category_enum(self):
        """Test NutritionalCategory enum."""
        assert NutritionalCategory.CARBOHYDRATES.value == "carbohydrates"
        assert NutritionalCategory.PROTEINS.value == "proteins"
        assert len(NutritionalCategory) == 6

    def test_food_class_info_creation(self):
        """Test FoodClassInfo dataclass."""
        food_info = FoodClassInfo(
            name="jollof_rice",
            local_names=["jollof"],
            nutritional_category=NutritionalCategory.CARBOHYDRATES,
            cultural_context="Popular rice dish"
        )

        assert food_info.name == "jollof_rice"
        assert food_info.nutritional_category == NutritionalCategory.CARBOHYDRATES

    def test_nigerian_food_mapper_init(self):
        """Test NigerianFoodMapper initialization."""
        mapper = NigerianFoodMapper()

        assert len(mapper.food_classes) > 0
        assert len(mapper.name_to_class) > 0
        assert len(mapper.nutritional_mapping) > 0

    def test_add_food_class(self):
        """Test adding food class to mapper."""
        mapper = NigerianFoodMapper()

        food_info = FoodClassInfo(
            name="test_food",
            local_names=["test"],
            nutritional_category=NutritionalCategory.PROTEINS
        )

        initial_count = len(mapper.food_classes)
        mapper.add_food_class(food_info)

        assert len(mapper.food_classes) == initial_count + 1
        assert "test_food" in mapper.food_classes
        assert mapper.name_to_class["test"] == "test_food"

    def test_get_food_class(self):
        """Test retrieving food class information."""
        mapper = NigerianFoodMapper()

        # Test with known food
        food_info = mapper.get_food_class("jollof_rice")
        assert food_info is not None
        assert food_info.name == "jollof_rice"

        # Test with local name
        food_info = mapper.get_food_class("jollof")
        assert food_info is not None

        # Test with unknown food
        food_info = mapper.get_food_class("unknown_food")
        assert food_info is None

    def test_get_nutritional_category(self):
        """Test getting nutritional category."""
        mapper = NigerianFoodMapper()

        category = mapper.get_nutritional_category("jollof_rice")
        assert category == NutritionalCategory.CARBOHYDRATES

        category = mapper.get_nutritional_category("unknown_food")
        assert category is None

    def test_get_classes_by_category(self):
        """Test getting classes by nutritional category."""
        mapper = NigerianFoodMapper()

        carb_classes = mapper.get_classes_by_category(
            NutritionalCategory.CARBOHYDRATES)
        protein_classes = mapper.get_classes_by_category(
            NutritionalCategory.PROTEINS)

        assert len(carb_classes) > 0
        assert len(protein_classes) > 0
        assert "jollof_rice" in carb_classes
        assert "beans" in protein_classes

    def test_model_class_mapping(self):
        """Test model class mapping creation."""
        mapper = NigerianFoodMapper()

        idx_to_class = mapper.create_model_class_mapping()
        class_to_idx = mapper.create_reverse_model_mapping()

        assert len(idx_to_class) == len(mapper.food_classes)
        assert len(class_to_idx) == len(mapper.food_classes)

        # Test bidirectional mapping
        for idx, class_name in idx_to_class.items():
            assert class_to_idx[class_name] == idx

    def test_analyze_meal_nutrition(self):
        """Test meal nutrition analysis."""
        mapper = NigerianFoodMapper()

        detected_foods = [
            ("jollof_rice", 0.9),
            ("beans", 0.8),
            ("unknown_food", 0.7)
        ]

        analysis = mapper.analyze_meal_nutrition(detected_foods)

        assert 'detected_foods' in analysis
        assert 'category_distribution' in analysis
        assert 'missing_categories' in analysis
        assert 'balance_score' in analysis

        assert len(analysis['detected_foods']) == 2  # Only known foods
        assert analysis['balance_score'] > 0

    def test_get_recommendations(self):
        """Test getting recommendations for missing categories."""
        mapper = NigerianFoodMapper()

        missing_categories = ["vitamins", "fats_oils"]
        recommendations = mapper.get_recommendations_for_missing_categories(
            missing_categories)

        assert isinstance(recommendations, dict)
        for category in missing_categories:
            if category in recommendations:
                assert isinstance(recommendations[category], list)

    def test_create_sample_metadata_file(self):
        """Test sample metadata file creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            create_sample_metadata_file(output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert 'foods' in data
            assert len(data['foods']) > 0

        finally:
            output_path.unlink()

    def test_export_mappings(self):
        """Test exporting food mappings."""
        mapper = NigerianFoodMapper()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            mapper.export_mappings(output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert 'food_classes' in data
            assert 'nutritional_categories' in data
            assert 'model_class_mapping' in data

        finally:
            output_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])
