"""
Dataset validation and quality checking tools for Nigerian food dataset.
Provides utilities to validate dataset integrity, image quality, and class distribution.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from collections import Counter, defaultdict

import torch
from PIL import Image
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ImageQualityMetrics:
    """Metrics for image quality assessment."""
    path: str
    width: int
    height: int
    channels: int
    file_size: int
    is_corrupted: bool
    brightness_mean: float
    contrast_std: float
    blur_score: float
    aspect_ratio: float


@dataclass
class DatasetValidationReport:
    """Comprehensive dataset validation report."""
    total_images: int
    corrupted_images: int
    missing_images: int
    class_distribution: Dict[str, int]
    quality_issues: List[str]
    recommendations: List[str]
    split_distribution: Dict[str, Dict[str, int]]
    image_quality_stats: Dict[str, float]


class ImageQualityChecker:
    """Utility class for checking image quality."""

    def __init__(
        self,
        min_resolution: Tuple[int, int] = (224, 224),
        max_file_size_mb: float = 10.0,
        min_brightness: float = 0.1,
        max_brightness: float = 0.9,
        min_contrast: float = 20.0
    ):
        """
        Initialize quality checker with thresholds.

        Args:
            min_resolution: Minimum (width, height) resolution
            max_file_size_mb: Maximum file size in MB
            min_brightness: Minimum acceptable brightness (0-1)
            max_brightness: Maximum acceptable brightness (0-1)
            min_contrast: Minimum acceptable contrast (std deviation)
        """
        self.min_resolution = min_resolution
        self.max_file_size_mb = max_file_size_mb
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.min_contrast = min_contrast

    def check_image_quality(self, image_path: Path) -> ImageQualityMetrics:
        """
        Check quality metrics for a single image.

        Args:
            image_path: Path to image file

        Returns:
            ImageQualityMetrics object with quality assessment
        """
        try:
            # Basic file info
            file_size = image_path.stat().st_size

            # Load and analyze image
            with Image.open(image_path) as img:
                width, height = img.size
                channels = len(img.getbands())

                # Convert to RGB for analysis
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Calculate quality metrics
                img_array = np.array(img)

                # Brightness (mean of grayscale)
                gray = np.mean(img_array, axis=2)
                brightness_mean = np.mean(gray) / 255.0

                # Contrast (std of grayscale)
                contrast_std = np.std(gray)

                # Simple blur detection (Laplacian variance)
                blur_score = self._calculate_blur_score(gray)

                # Aspect ratio
                aspect_ratio = width / height

                return ImageQualityMetrics(
                    path=str(image_path),
                    width=width,
                    height=height,
                    channels=channels,
                    file_size=file_size,
                    is_corrupted=False,
                    brightness_mean=brightness_mean,
                    contrast_std=contrast_std,
                    blur_score=blur_score,
                    aspect_ratio=aspect_ratio
                )

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return ImageQualityMetrics(
                path=str(image_path),
                width=0,
                height=0,
                channels=0,
                file_size=0,
                is_corrupted=True,
                brightness_mean=0.0,
                contrast_std=0.0,
                blur_score=0.0,
                aspect_ratio=0.0
            )

    def _calculate_blur_score(self, gray_image: np.ndarray) -> float:
        """Calculate blur score using Laplacian variance."""
        try:
            # Simple Laplacian kernel
            laplacian_kernel = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]])

            # Apply convolution manually (simplified)
            h, w = gray_image.shape
            result = np.zeros_like(gray_image)

            for i in range(1, h-1):
                for j in range(1, w-1):
                    result[i, j] = np.sum(
                        gray_image[i-1:i+2, j-1:j+2] * laplacian_kernel)

            return float(np.var(result))
        except Exception:
            return 0.0

    def is_quality_acceptable(self, metrics: ImageQualityMetrics) -> Tuple[bool, List[str]]:
        """
        Check if image quality meets acceptance criteria.

        Args:
            metrics: Image quality metrics

        Returns:
            Tuple of (is_acceptable, list_of_issues)
        """
        issues = []

        if metrics.is_corrupted:
            issues.append("Image is corrupted or unreadable")

        if metrics.width < self.min_resolution[0] or metrics.height < self.min_resolution[1]:
            issues.append(
                f"Resolution too low: {metrics.width}x{metrics.height}")

        if metrics.file_size > self.max_file_size_mb * 1024 * 1024:
            issues.append(
                f"File size too large: {metrics.file_size / (1024*1024):.1f}MB")

        if metrics.brightness_mean < self.min_brightness:
            issues.append(
                f"Image too dark: brightness {metrics.brightness_mean:.2f}")

        if metrics.brightness_mean > self.max_brightness:
            issues.append(
                f"Image too bright: brightness {metrics.brightness_mean:.2f}")

        if metrics.contrast_std < self.min_contrast:
            issues.append(f"Low contrast: {metrics.contrast_std:.1f}")

        if metrics.blur_score < 100:  # Threshold for blur detection
            issues.append(
                f"Image appears blurry: score {metrics.blur_score:.1f}")

        return len(issues) == 0, issues


class DatasetValidator:
    """Main class for validating Nigerian food dataset."""

    def __init__(self, dataset_root: Path):
        """
        Initialize dataset validator.

        Args:
            dataset_root: Path to dataset root directory
        """
        self.dataset_root = Path(dataset_root)
        self.quality_checker = ImageQualityChecker()

    def validate_dataset_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate that dataset has the expected directory structure.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check required directories
        required_dirs = [
            "images/train",
            "images/val",
            "images/test",
            "metadata"
        ]

        for dir_path in required_dirs:
            full_path = self.dataset_root / dir_path
            if not full_path.exists():
                issues.append(f"Missing required directory: {dir_path}")
            elif not full_path.is_dir():
                issues.append(
                    f"Path exists but is not a directory: {dir_path}")

        # Check metadata file
        metadata_file = self.dataset_root / "metadata" / "nigerian_foods.json"
        if not metadata_file.exists():
            issues.append(
                "Missing metadata file: metadata/nigerian_foods.json")

        return len(issues) == 0, issues

    def validate_metadata(self) -> Tuple[bool, List[str]]:
        """
        Validate metadata file structure and content.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        metadata_file = self.dataset_root / "metadata" / "nigerian_foods.json"

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Check required top-level keys
            if 'foods' not in metadata:
                issues.append("Metadata missing 'foods' key")
                return False, issues

            # Validate each food item
            required_fields = ['name', 'food_class', 'nutritional_category']

            for i, food_item in enumerate(metadata['foods']):
                for field in required_fields:
                    if field not in food_item:
                        issues.append(
                            f"Food item {i} missing required field: {field}")

                # Check for valid nutritional categories
                valid_categories = [
                    'carbohydrates', 'proteins', 'fats_oils',
                    'vitamins', 'minerals', 'water'
                ]
                if food_item.get('nutritional_category') not in valid_categories:
                    issues.append(
                        f"Invalid nutritional category for {food_item.get('name', f'item {i}')}")

        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON in metadata file: {e}")
        except Exception as e:
            issues.append(f"Error reading metadata file: {e}")

        return len(issues) == 0, issues

    def check_class_distribution(self) -> Dict[str, Dict[str, int]]:
        """
        Check class distribution across train/val/test splits.

        Returns:
            Dictionary with split -> class -> count mapping
        """
        distribution = defaultdict(lambda: defaultdict(int))

        for split in ['train', 'val', 'test']:
            split_dir = self.dataset_root / "images" / split
            if split_dir.exists():
                for class_dir in split_dir.iterdir():
                    if class_dir.is_dir():
                        # Count images in class directory
                        image_count = len([
                            f for f in class_dir.iterdir()
                            if f.suffix.lower() in ['.jpg', '.jpeg', '.png']
                        ])
                        distribution[split][class_dir.name] = image_count

        return dict(distribution)

    def validate_images(self, sample_size: Optional[int] = None) -> List[ImageQualityMetrics]:
        """
        Validate image quality across the dataset.

        Args:
            sample_size: If provided, randomly sample this many images per split

        Returns:
            List of quality metrics for all checked images
        """
        all_metrics = []

        for split in ['train', 'val', 'test']:
            split_dir = self.dataset_root / "images" / split
            if not split_dir.exists():
                continue

            # Collect all image paths
            image_paths = []
            for class_dir in split_dir.iterdir():
                if class_dir.is_dir():
                    for img_path in class_dir.iterdir():
                        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            image_paths.append(img_path)

            # Sample if requested
            if sample_size and len(image_paths) > sample_size:
                import random
                image_paths = random.sample(image_paths, sample_size)

            # Check quality for each image
            for img_path in image_paths:
                metrics = self.quality_checker.check_image_quality(img_path)
                all_metrics.append(metrics)

        return all_metrics

    def generate_validation_report(self, sample_size: Optional[int] = 100) -> DatasetValidationReport:
        """
        Generate comprehensive validation report.

        Args:
            sample_size: Number of images to sample for quality checking

        Returns:
            DatasetValidationReport with all validation results
        """
        logger.info("Starting dataset validation...")

        # Structure validation
        structure_valid, structure_issues = self.validate_dataset_structure()

        # Metadata validation
        metadata_valid, metadata_issues = self.validate_metadata()

        # Class distribution
        class_distribution = self.check_class_distribution()

        # Image quality validation
        quality_metrics = self.validate_images(sample_size)

        # Aggregate statistics
        total_images = len(quality_metrics)
        corrupted_images = sum(1 for m in quality_metrics if m.is_corrupted)

        # Calculate quality statistics
        valid_metrics = [m for m in quality_metrics if not m.is_corrupted]
        if valid_metrics:
            quality_stats = {
                'mean_brightness': np.mean([m.brightness_mean for m in valid_metrics]),
                'mean_contrast': np.mean([m.contrast_std for m in valid_metrics]),
                'mean_blur_score': np.mean([m.blur_score for m in valid_metrics]),
                'mean_aspect_ratio': np.mean([m.aspect_ratio for m in valid_metrics])
            }
        else:
            quality_stats = {}

        # Compile all issues and recommendations
        all_issues = structure_issues + metadata_issues

        recommendations = []
        if corrupted_images > 0:
            recommendations.append(
                f"Remove or fix {corrupted_images} corrupted images")

        if not structure_valid:
            recommendations.append("Fix dataset directory structure")

        if not metadata_valid:
            recommendations.append("Fix metadata file issues")

        # Check class balance
        total_per_class = defaultdict(int)
        for split_data in class_distribution.values():
            for class_name, count in split_data.items():
                total_per_class[class_name] += count

        if total_per_class:
            min_count = min(total_per_class.values())
            max_count = max(total_per_class.values())
            if max_count > min_count * 3:  # Imbalance threshold
                recommendations.append("Consider balancing class distribution")

        return DatasetValidationReport(
            total_images=total_images,
            corrupted_images=corrupted_images,
            missing_images=0,  # Would need more complex logic to detect
            class_distribution=dict(total_per_class),
            quality_issues=all_issues,
            recommendations=recommendations,
            split_distribution=class_distribution,
            image_quality_stats=quality_stats
        )

    def save_validation_report(self, report: DatasetValidationReport, output_path: Path):
        """Save validation report to JSON file."""
        report_dict = {
            'total_images': report.total_images,
            'corrupted_images': report.corrupted_images,
            'missing_images': report.missing_images,
            'class_distribution': report.class_distribution,
            'quality_issues': report.quality_issues,
            'recommendations': report.recommendations,
            'split_distribution': report.split_distribution,
            'image_quality_stats': report.image_quality_stats
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Validation report saved to {output_path}")
