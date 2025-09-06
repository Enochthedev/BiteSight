"""
Data loading utilities for Nigerian food images.
Handles loading, organizing, and preparing Nigerian food dataset for training.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import logging

import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FoodItem:
    """Represents a Nigerian food item with metadata."""
    name: str
    local_names: List[str]
    food_class: str
    image_paths: List[str]
    nutritional_category: str
    cultural_context: Optional[str] = None


class NigerianFoodDataset(Dataset):
    """PyTorch Dataset for Nigerian food images."""

    def __init__(
        self,
        data_dir: Union[str, Path],
        transform=None,
        target_transform=None,
        split: str = "train"
    ):
        """
        Initialize Nigerian food dataset.

        Args:
            data_dir: Path to dataset directory
            transform: Image transformations to apply
            target_transform: Target transformations to apply
            split: Dataset split ('train', 'val', 'test')
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.target_transform = target_transform
        self.split = split

        # Load dataset metadata
        self.food_items = self._load_food_metadata()
        self.class_to_idx = self._create_class_mapping()
        self.samples = self._load_samples()

        logger.info(f"Loaded {len(self.samples)} samples for {split} split")
        logger.info(f"Found {len(self.class_to_idx)} food classes")

    def _load_food_metadata(self) -> Dict[str, FoodItem]:
        """Load food metadata from JSON file."""
        metadata_path = self.data_dir / "metadata" / "nigerian_foods.json"

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        food_items = {}
        for item_data in metadata['foods']:
            food_item = FoodItem(
                name=item_data['name'],
                local_names=item_data.get('local_names', []),
                food_class=item_data['food_class'],
                image_paths=item_data.get('image_paths', []),
                nutritional_category=item_data['nutritional_category'],
                cultural_context=item_data.get('cultural_context')
            )
            food_items[food_item.name] = food_item

        return food_items

    def _create_class_mapping(self) -> Dict[str, int]:
        """Create mapping from food class names to indices."""
        unique_classes = sorted(set(
            item.food_class for item in self.food_items.values()
        ))
        return {cls_name: idx for idx, cls_name in enumerate(unique_classes)}

    def _load_samples(self) -> List[Tuple[str, int]]:
        """Load image paths and corresponding class indices."""
        samples = []
        split_dir = self.data_dir / "images" / self.split

        if not split_dir.exists():
            raise FileNotFoundError(f"Split directory not found: {split_dir}")

        for food_name, food_item in self.food_items.items():
            class_idx = self.class_to_idx[food_item.food_class]
            food_dir = split_dir / food_name.replace(' ', '_').lower()

            if food_dir.exists():
                for img_path in food_dir.glob("*.jpg"):
                    samples.append((str(img_path), class_idx))
                for img_path in food_dir.glob("*.png"):
                    samples.append((str(img_path), class_idx))

        return samples

    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """Get a sample from the dataset."""
        img_path, target = self.samples[idx]

        # Load image
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            logger.error(f"Error loading image {img_path}: {e}")
            # Return a black image as fallback
            image = Image.new('RGB', (224, 224), color='black')

        # Apply transformations
        if self.transform:
            image = self.transform(image)

        if self.target_transform:
            target = self.target_transform(target)

        return image, target

    def get_class_names(self) -> List[str]:
        """Get list of class names in order."""
        return [cls for cls, _ in sorted(self.class_to_idx.items(), key=lambda x: x[1])]

    def get_food_info(self, class_name: str) -> Optional[FoodItem]:
        """Get food item information by class name."""
        for food_item in self.food_items.values():
            if food_item.food_class == class_name:
                return food_item
        return None


class DatasetLoader:
    """Utility class for loading and managing Nigerian food datasets."""

    def __init__(self, data_dir: Union[str, Path]):
        """
        Initialize dataset loader.

        Args:
            data_dir: Path to dataset root directory
        """
        self.data_dir = Path(data_dir)
        self._validate_dataset_structure()

    def _validate_dataset_structure(self):
        """Validate that dataset has required structure."""
        required_dirs = [
            "images/train",
            "images/val",
            "images/test",
            "metadata"
        ]

        for dir_path in required_dirs:
            full_path = self.data_dir / dir_path
            if not full_path.exists():
                raise FileNotFoundError(
                    f"Required directory not found: {full_path}")

        # Check for metadata file
        metadata_file = self.data_dir / "metadata" / "nigerian_foods.json"
        if not metadata_file.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_file}")

    def create_dataloaders(
        self,
        batch_size: int = 32,
        num_workers: int = 4,
        train_transform=None,
        val_transform=None
    ) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Create train, validation, and test dataloaders.

        Args:
            batch_size: Batch size for dataloaders
            num_workers: Number of worker processes
            train_transform: Transformations for training data
            val_transform: Transformations for validation/test data

        Returns:
            Tuple of (train_loader, val_loader, test_loader)
        """
        # Create datasets
        train_dataset = NigerianFoodDataset(
            self.data_dir, transform=train_transform, split="train"
        )
        val_dataset = NigerianFoodDataset(
            self.data_dir, transform=val_transform, split="val"
        )
        test_dataset = NigerianFoodDataset(
            self.data_dir, transform=val_transform, split="test"
        )

        # Create dataloaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )

        return train_loader, val_loader, test_loader

    def get_dataset_statistics(self) -> Dict[str, any]:
        """Get statistics about the dataset."""
        stats = {}

        for split in ["train", "val", "test"]:
            dataset = NigerianFoodDataset(self.data_dir, split=split)
            stats[split] = {
                "num_samples": len(dataset),
                "num_classes": len(dataset.class_to_idx),
                "class_names": dataset.get_class_names()
            }

        return stats
