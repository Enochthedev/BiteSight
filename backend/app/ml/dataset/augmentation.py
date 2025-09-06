"""
Image augmentation pipeline for Nigerian food dataset training.
Implements data augmentation strategies optimized for food recognition.
"""

import random
from typing import Callable, List, Optional, Tuple
import logging

import torch
import torchvision.transforms as transforms
from torchvision.transforms import functional as F
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

logger = logging.getLogger(__name__)


class FoodAugmentation:
    """Custom augmentation transforms for food images."""

    @staticmethod
    def random_lighting(image: Image.Image, brightness_range: Tuple[float, float] = (0.8, 1.2)) -> Image.Image:
        """Apply random brightness adjustment to simulate different lighting conditions."""
        factor = random.uniform(*brightness_range)
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    @staticmethod
    def random_contrast(image: Image.Image, contrast_range: Tuple[float, float] = (0.8, 1.2)) -> Image.Image:
        """Apply random contrast adjustment."""
        factor = random.uniform(*contrast_range)
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    @staticmethod
    def random_saturation(image: Image.Image, saturation_range: Tuple[float, float] = (0.8, 1.2)) -> Image.Image:
        """Apply random saturation adjustment to handle color variations."""
        factor = random.uniform(*saturation_range)
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)

    @staticmethod
    def random_blur(image: Image.Image, blur_probability: float = 0.1) -> Image.Image:
        """Apply random blur to simulate camera focus issues."""
        if random.random() < blur_probability:
            radius = random.uniform(0.5, 1.5)
            return image.filter(ImageFilter.GaussianBlur(radius=radius))
        return image

    @staticmethod
    def random_noise(image: Image.Image, noise_probability: float = 0.1, noise_factor: float = 0.1) -> Image.Image:
        """Add random noise to simulate low-quality camera conditions."""
        if random.random() < noise_probability:
            np_image = np.array(image)
            noise = np.random.normal(
                0, noise_factor * 255, np_image.shape).astype(np.uint8)
            noisy_image = np.clip(np_image.astype(
                np.int16) + noise, 0, 255).astype(np.uint8)
            return Image.fromarray(noisy_image)
        return image


class FoodSpecificTransform:
    """Transform that applies food-specific augmentations."""

    def __init__(
        self,
        brightness_range: Tuple[float, float] = (0.8, 1.2),
        contrast_range: Tuple[float, float] = (0.8, 1.2),
        saturation_range: Tuple[float, float] = (0.8, 1.2),
        blur_probability: float = 0.1,
        noise_probability: float = 0.1
    ):
        self.brightness_range = brightness_range
        self.contrast_range = contrast_range
        self.saturation_range = saturation_range
        self.blur_probability = blur_probability
        self.noise_probability = noise_probability

    def __call__(self, image: Image.Image) -> Image.Image:
        """Apply food-specific augmentations."""
        # Apply lighting variations (common in mobile photography)
        image = FoodAugmentation.random_lighting(image, self.brightness_range)
        image = FoodAugmentation.random_contrast(image, self.contrast_range)
        image = FoodAugmentation.random_saturation(
            image, self.saturation_range)

        # Apply quality degradations
        image = FoodAugmentation.random_blur(image, self.blur_probability)
        image = FoodAugmentation.random_noise(image, self.noise_probability)

        return image


def get_training_transforms(
    input_size: int = 224,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> transforms.Compose:
    """
    Get training data augmentation pipeline.

    Args:
        input_size: Target image size
        mean: ImageNet normalization mean
        std: ImageNet normalization std

    Returns:
        Composed transform pipeline
    """
    return transforms.Compose([
        # Resize with some randomness
        transforms.RandomResizedCrop(
            input_size,
            scale=(0.8, 1.0),
            ratio=(0.8, 1.2),
            interpolation=transforms.InterpolationMode.BILINEAR
        ),

        # Random horizontal flip (food plates can be mirrored)
        transforms.RandomHorizontalFlip(p=0.5),

        # Random rotation (slight angle variations in photos)
        transforms.RandomRotation(
            degrees=15, interpolation=transforms.InterpolationMode.BILINEAR),

        # Food-specific augmentations
        FoodSpecificTransform(
            brightness_range=(0.7, 1.3),
            contrast_range=(0.8, 1.2),
            saturation_range=(0.8, 1.2),
            blur_probability=0.1,
            noise_probability=0.1
        ),

        # Convert to tensor and normalize
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),

        # Random erasing (simulate occlusion)
        transforms.RandomErasing(
            p=0.1,
            scale=(0.02, 0.1),
            ratio=(0.3, 3.3),
            value='random'
        )
    ])


def get_validation_transforms(
    input_size: int = 224,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> transforms.Compose:
    """
    Get validation/test data preprocessing pipeline.

    Args:
        input_size: Target image size
        mean: ImageNet normalization mean
        std: ImageNet normalization std

    Returns:
        Composed transform pipeline
    """
    return transforms.Compose([
        transforms.Resize(int(input_size * 1.14)),  # Resize to slightly larger
        # Center crop to target size
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])


def get_inference_transforms(
    input_size: int = 224,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> transforms.Compose:
    """
    Get inference preprocessing pipeline for production use.

    Args:
        input_size: Target image size
        mean: ImageNet normalization mean
        std: ImageNet normalization std

    Returns:
        Composed transform pipeline
    """
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])


class AugmentationConfig:
    """Configuration class for augmentation parameters."""

    def __init__(
        self,
        input_size: int = 224,
        horizontal_flip_prob: float = 0.5,
        rotation_degrees: float = 15,
        brightness_range: Tuple[float, float] = (0.7, 1.3),
        contrast_range: Tuple[float, float] = (0.8, 1.2),
        saturation_range: Tuple[float, float] = (0.8, 1.2),
        blur_probability: float = 0.1,
        noise_probability: float = 0.1,
        random_erasing_prob: float = 0.1,
        mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
    ):
        self.input_size = input_size
        self.horizontal_flip_prob = horizontal_flip_prob
        self.rotation_degrees = rotation_degrees
        self.brightness_range = brightness_range
        self.contrast_range = contrast_range
        self.saturation_range = saturation_range
        self.blur_probability = blur_probability
        self.noise_probability = noise_probability
        self.random_erasing_prob = random_erasing_prob
        self.mean = mean
        self.std = std

    def get_training_transforms(self) -> transforms.Compose:
        """Get training transforms with current configuration."""
        return transforms.Compose([
            transforms.RandomResizedCrop(
                self.input_size,
                scale=(0.8, 1.0),
                ratio=(0.8, 1.2)
            ),
            transforms.RandomHorizontalFlip(p=self.horizontal_flip_prob),
            transforms.RandomRotation(degrees=self.rotation_degrees),
            FoodSpecificTransform(
                brightness_range=self.brightness_range,
                contrast_range=self.contrast_range,
                saturation_range=self.saturation_range,
                blur_probability=self.blur_probability,
                noise_probability=self.noise_probability
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=self.mean, std=self.std),
            transforms.RandomErasing(p=self.random_erasing_prob)
        ])

    def get_validation_transforms(self) -> transforms.Compose:
        """Get validation transforms with current configuration."""
        return get_validation_transforms(
            input_size=self.input_size,
            mean=self.mean,
            std=self.std
        )
