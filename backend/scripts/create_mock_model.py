#!/usr/bin/env python3
"""
Create a mock model for MVP testing.
This creates a valid PyTorch model file that can be loaded by the inference system.
"""

import torch
import argparse
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.models.mobilenet_food_classifier import MobileNetV2FoodClassifier


def create_mock_model(num_classes: int, class_names: list, output_path: str):
    """
    Create a mock model with random weights for testing.
    
    Args:
        num_classes: Number of food classes
        class_names: List of class names
        output_path: Where to save the model
    """
    print(f"Creating mock model with {num_classes} classes...")
    
    # Create model
    model = MobileNetV2FoodClassifier(
        num_classes=num_classes,
        pretrained=False,  # Don't download ImageNet weights
        dropout=0.2
    )
    
    # Create checkpoint with metadata
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'num_classes': num_classes,
        'model_type': 'MobileNetV2FoodClassifier',
        'version': '1.0.0-mock',
        'description': 'Mock model for MVP testing - uses random weights',
        'training_info': {
            'epochs': 0,
            'best_accuracy': 0.0,
            'note': 'This is a mock model for testing purposes only'
        }
    }
    
    # Save model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    torch.save(checkpoint, output_path)
    
    print(f"✓ Mock model saved to: {output_path}")
    print(f"  Model size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Classes: {num_classes}")
    print("\n⚠️  WARNING: This is a MOCK model with random weights!")
    print("   It will produce random predictions for testing purposes.")
    print("   Train a real model for production use.")


def download_pretrained_model(output_path: str, class_names: list):
    """
    Download and adapt a pre-trained MobileNetV2 model.
    Uses ImageNet weights as a starting point.
    
    Args:
        output_path: Where to save the model
        class_names: List of class names
    """
    print("Downloading pre-trained MobileNetV2 (ImageNet weights)...")
    
    num_classes = len(class_names)
    
    # Create model with ImageNet pre-trained weights
    model = MobileNetV2FoodClassifier(
        num_classes=num_classes,
        pretrained=True,  # Download ImageNet weights
        dropout=0.2
    )
    
    # Create checkpoint
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'num_classes': num_classes,
        'model_type': 'MobileNetV2FoodClassifier',
        'version': '1.0.0-pretrained',
        'description': 'Pre-trained MobileNetV2 with ImageNet weights, adapted for Nigerian foods',
        'training_info': {
            'epochs': 0,
            'best_accuracy': 0.0,
            'base_model': 'ImageNet MobileNetV2',
            'note': 'Requires fine-tuning on Nigerian food dataset'
        }
    }
    
    # Save model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    torch.save(checkpoint, output_path)
    
    print(f"✓ Pre-trained model saved to: {output_path}")
    print(f"  Model size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Classes: {num_classes}")
    print("\n✓ This model has ImageNet pre-trained weights")
    print("  Fine-tune it on your Nigerian food dataset for best results.")


def main():
    parser = argparse.ArgumentParser(description='Create model for MVP')
    parser.add_argument('--output', type=str, default='models/best_model.pth',
                       help='Output model file path')
    parser.add_argument('--food-mapping', type=str, 
                       default='dataset/metadata/nigerian_foods.json',
                       help='Food mapping JSON file')
    parser.add_argument('--mode', type=str, choices=['mock', 'pretrained'],
                       default='pretrained',
                       help='Model creation mode: mock (random) or pretrained (ImageNet)')
    parser.add_argument('--num-classes', type=int, default=None,
                       help='Number of classes (auto-detected from mapping if not provided)')
    
    args = parser.parse_args()
    
    # Load food mapping to get class names
    mapping_path = Path(args.food_mapping)
    
    if mapping_path.exists():
        print(f"Loading food mapping from: {args.food_mapping}")
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)
        
        # Get class names from mapping
        class_names = list(mapping['foods'].keys())
        num_classes = len(class_names)
        
        print(f"Found {num_classes} food classes in mapping")
    else:
        print(f"⚠️  Food mapping not found: {args.food_mapping}")
        
        if args.num_classes:
            num_classes = args.num_classes
            class_names = [f"class_{i}" for i in range(num_classes)]
            print(f"Using {num_classes} generic classes")
        else:
            print("ERROR: Either provide --food-mapping or --num-classes")
            return
    
    # Create model based on mode
    if args.mode == 'mock':
        create_mock_model(num_classes, class_names, args.output)
    else:
        download_pretrained_model(args.output, class_names)


if __name__ == '__main__':
    main()
