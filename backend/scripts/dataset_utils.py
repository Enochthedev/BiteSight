#!/usr/bin/env python3
"""
Dataset utilities script for Nigerian food recognition.
Provides command-line tools for dataset validation, statistics, and setup.
"""

from app.ml.dataset.data_loader import DatasetLoader
from app.ml.dataset.validation import DatasetValidator
from app.ml.dataset.food_mapping import NigerianFoodMapper, create_sample_metadata_file
from app.ml.dataset.augmentation import AugmentationConfig
from app.ml.dataset.augmentation import AugmentationConfig
from app.ml.dataset.food_mapping import NigerianFoodMapper, create_sample_metadata_file
from app.ml.dataset.validation import DatasetValidator
import argparse
import sys
from pathlib import Path
import json
import logging

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_dataset(dataset_path: Path, sample_size: int = 100):
    """Validate dataset and generate report."""
    logger.info(f"Validating dataset at {dataset_path}")

    try:
        validator = DatasetValidator(dataset_path)
        report = validator.generate_validation_report(sample_size=sample_size)

        # Print summary
        print("\n" + "="*50)
        print("DATASET VALIDATION REPORT")
        print("="*50)

        print(f"Total images checked: {report.total_images}")
        print(f"Corrupted images: {report.corrupted_images}")
        print(f"Class distribution: {report.class_distribution}")

        if report.quality_issues:
            print(f"\nQuality Issues ({len(report.quality_issues)}):")
            for issue in report.quality_issues:
                print(f"  - {issue}")

        if report.recommendations:
            print(f"\nRecommendations ({len(report.recommendations)}):")
            for rec in report.recommendations:
                print(f"  - {rec}")

        print(f"\nSplit Distribution:")
        for split, classes in report.split_distribution.items():
            total = sum(classes.values())
            print(f"  {split}: {total} images across {len(classes)} classes")

        if report.image_quality_stats:
            print(f"\nImage Quality Statistics:")
            for stat, value in report.image_quality_stats.items():
                print(f"  {stat}: {value:.3f}")

        # Save detailed report
        report_path = dataset_path / "validation_report.json"
        validator.save_validation_report(report, report_path)
        print(f"\nDetailed report saved to: {report_path}")

        return len(report.quality_issues) == 0

    except Exception as e:
        logger.error(f"Error validating dataset: {e}")
        return False


def show_dataset_stats(dataset_path: Path):
    """Show dataset statistics."""
    logger.info(f"Analyzing dataset at {dataset_path}")

    try:
        loader = DatasetLoader(dataset_path)
        stats = loader.get_dataset_statistics()

        print("\n" + "="*50)
        print("DATASET STATISTICS")
        print("="*50)

        total_images = 0
        total_classes = set()

        for split, split_stats in stats.items():
            print(f"\n{split.upper()} Split:")
            print(f"  Images: {split_stats['num_samples']}")
            print(f"  Classes: {split_stats['num_classes']}")
            print(
                f"  Class names: {', '.join(split_stats['class_names'][:5])}...")

            total_images += split_stats['num_samples']
            total_classes.update(split_stats['class_names'])

        print(f"\nOVERALL:")
        print(f"  Total images: {total_images}")
        print(f"  Total unique classes: {len(total_classes)}")

    except Exception as e:
        logger.error(f"Error analyzing dataset: {e}")


def test_food_mapping(metadata_path: Path):
    """Test food mapping functionality."""
    logger.info(f"Testing food mapping with {metadata_path}")

    try:
        mapper = NigerianFoodMapper(metadata_path)

        print("\n" + "="*50)
        print("FOOD MAPPING TEST")
        print("="*50)

        print(f"Loaded {len(mapper.get_all_classes())} food classes")

        # Test some mappings
        test_foods = ["jollof_rice", "jollof", "beans", "ewa", "unknown_food"]

        print(f"\nTesting food recognition:")
        for food in test_foods:
            food_info = mapper.get_food_class(food)
            if food_info:
                print(
                    f"  '{food}' -> {food_info.name} ({food_info.nutritional_category.value})")
            else:
                print(f"  '{food}' -> Not found")

        # Test meal analysis
        sample_meal = [("jollof_rice", 0.9), ("beans", 0.8), ("plantain", 0.7)]
        analysis = mapper.analyze_meal_nutrition(sample_meal)

        print(f"\nSample meal analysis:")
        print(f"  Detected foods: {len(analysis['detected_foods'])}")
        print(f"  Balance score: {analysis['balance_score']:.2f}")
        print(f"  Missing categories: {analysis['missing_categories']}")

        # Get recommendations
        if analysis['missing_categories']:
            recommendations = mapper.get_recommendations_for_missing_categories(
                analysis['missing_categories']
            )
            print(f"  Recommendations: {recommendations}")

    except Exception as e:
        logger.error(f"Error testing food mapping: {e}")


def create_sample_dataset(output_path: Path):
    """Create sample dataset structure and metadata."""
    logger.info(f"Creating sample dataset at {output_path}")

    try:
        # Create directory structure
        for split in ['train', 'val', 'test']:
            (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)

        (output_path / 'metadata').mkdir(exist_ok=True)

        # Create sample metadata
        metadata_path = output_path / 'metadata' / 'nigerian_foods.json'
        create_sample_metadata_file(metadata_path)

        # Create sample class directories
        mapper = NigerianFoodMapper(metadata_path)
        food_classes = mapper.get_all_classes()

        for split in ['train', 'val', 'test']:
            # Create dirs for first 5 classes
            for food_class in food_classes[:5]:
                class_dir = output_path / 'images' / split / food_class
                class_dir.mkdir(exist_ok=True)

                # Create a README in each class directory
                readme_path = class_dir / 'README.md'
                with open(readme_path, 'w') as f:
                    f.write(f"# {food_class.replace('_', ' ').title()}\n\n")
                    f.write(f"Place {food_class} images in this directory.\n")
                    f.write(f"Supported formats: .jpg, .jpeg, .png\n")

        print(f"Sample dataset structure created at {output_path}")
        print(f"Metadata file: {metadata_path}")
        print(f"Add images to the appropriate class directories under images/train/, images/val/, images/test/")

    except Exception as e:
        logger.error(f"Error creating sample dataset: {e}")


def test_augmentation():
    """Test augmentation pipeline."""
    logger.info("Testing augmentation pipeline")

    try:
        from PIL import Image
        import torch

        # Create sample image
        sample_image = Image.new('RGB', (256, 256), color='blue')

        # Test augmentation config
        config = AugmentationConfig()
        train_transforms = config.get_training_transforms()
        val_transforms = config.get_validation_transforms()

        # Apply transforms
        train_result = train_transforms(sample_image)
        val_result = val_transforms(sample_image)

        print("\n" + "="*50)
        print("AUGMENTATION TEST")
        print("="*50)

        print(f"Original image size: {sample_image.size}")
        print(f"Training transform output: {train_result.shape}")
        print(f"Validation transform output: {val_result.shape}")
        print(
            f"Training tensor range: [{train_result.min():.3f}, {train_result.max():.3f}]")
        print(
            f"Validation tensor range: [{val_result.min():.3f}, {val_result.max():.3f}]")

        print("Augmentation pipeline test completed successfully!")

    except Exception as e:
        logger.error(f"Error testing augmentation: {e}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Nigerian Food Dataset Utilities")
    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate', help='Validate dataset')
    validate_parser.add_argument(
        'dataset_path', type=Path, help='Path to dataset directory')
    validate_parser.add_argument('--sample-size', type=int, default=100,
                                 help='Number of images to sample for quality check')

    # Stats command
    stats_parser = subparsers.add_parser(
        'stats', help='Show dataset statistics')
    stats_parser.add_argument(
        'dataset_path', type=Path, help='Path to dataset directory')

    # Test mapping command
    mapping_parser = subparsers.add_parser(
        'test-mapping', help='Test food mapping')
    mapping_parser.add_argument(
        'metadata_path', type=Path, help='Path to metadata file')

    # Create sample command
    create_parser = subparsers.add_parser(
        'create-sample', help='Create sample dataset')
    create_parser.add_argument(
        'output_path', type=Path, help='Output directory for sample dataset')

    # Test augmentation command
    subparsers.add_parser('test-augmentation',
                          help='Test augmentation pipeline')

    args = parser.parse_args()

    if args.command == 'validate':
        success = validate_dataset(args.dataset_path, args.sample_size)
        sys.exit(0 if success else 1)

    elif args.command == 'stats':
        show_dataset_stats(args.dataset_path)

    elif args.command == 'test-mapping':
        test_food_mapping(args.metadata_path)

    elif args.command == 'create-sample':
        create_sample_dataset(args.output_path)

    elif args.command == 'test-augmentation':
        test_augmentation()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
