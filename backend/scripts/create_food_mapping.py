#!/usr/bin/env python3
"""
Create Nigerian food mapping JSON from CSV file.
Maps food names to nutritional categories and metadata.
"""

import csv
import json
import argparse
from pathlib import Path
from typing import Dict, List


def parse_csv_to_mapping(csv_path: str) -> Dict:
    """Parse Nigerian food CSV and create mapping structure."""
    
    food_mapping = {
        "version": "1.0",
        "description": "Nigerian food classification and nutritional mapping",
        "categories": {
            "carbohydrates": {
                "description": "Energy-providing foods",
                "color": "#FFB74D",
                "foods": []
            },
            "protein": {
                "description": "Body-building foods",
                "color": "#E57373",
                "foods": []
            },
            "fats_oils": {
                "description": "Energy and vitamin absorption",
                "color": "#FFF176",
                "foods": []
            },
            "vitamins": {
                "description": "Body-regulating foods",
                "color": "#81C784",
                "foods": []
            },
            "water": {
                "description": "Hydration",
                "color": "#64B5F6",
                "foods": []
            },
            "snacks": {
                "description": "Processed and snack foods",
                "color": "#BA68C8",
                "foods": []
            }
        },
        "foods": {}
    }
    
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            food_name = row['food_name'].strip()
            food_class = row['food_class'].strip().lower().replace(' ', '_').replace('&', 'and')
            primary_nutrients = row['primary_nutrients'].strip()
            additional_nutrients = row['additional_nutrients'].strip()
            preparation_method = row['preparation_method'].strip()
            
            # Create food entry
            food_id = food_name.lower().replace(' ', '_').replace('(', '').replace(')', '')
            
            food_entry = {
                "id": food_id,
                "name": food_name,
                "category": food_class,
                "primary_nutrients": [n.strip() for n in primary_nutrients.split(',') if n.strip()],
                "additional_nutrients": [n.strip() for n in additional_nutrients.split(',') if n.strip()],
                "preparation_method": preparation_method,
                "local_names": {},  # Can be populated later
                "description": f"{food_name} - {preparation_method}",
                "tags": [food_class, preparation_method.lower()]
            }
            
            # Add to foods dict
            food_mapping["foods"][food_id] = food_entry
            
            # Add to category
            if food_class in food_mapping["categories"]:
                food_mapping["categories"][food_class]["foods"].append(food_id)
    
    return food_mapping


def create_class_names_list(mapping: Dict) -> List[str]:
    """Create ordered list of class names for model training."""
    class_names = []
    
    # Sort by category then alphabetically
    for category in sorted(mapping["categories"].keys()):
        foods = mapping["categories"][category]["foods"]
        for food_id in sorted(foods):
            class_names.append(food_id)
    
    return class_names


def main():
    parser = argparse.ArgumentParser(description='Create food mapping from CSV')
    parser.add_argument('--csv', type=str, default='data/Nigerianfood.csv',
                       help='Path to Nigerian food CSV file')
    parser.add_argument('--output', type=str, default='dataset/metadata/nigerian_foods.json',
                       help='Output JSON file path')
    parser.add_argument('--class-names', type=str, default='dataset/metadata/class_names.txt',
                       help='Output class names text file')
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Parse CSV
    print(f"Reading CSV from: {args.csv}")
    mapping = parse_csv_to_mapping(args.csv)
    
    # Save JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created food mapping: {args.output}")
    print(f"  Total foods: {len(mapping['foods'])}")
    print(f"  Categories: {len(mapping['categories'])}")
    
    for category, data in mapping['categories'].items():
        print(f"    - {category}: {len(data['foods'])} foods")
    
    # Create class names list
    class_names = create_class_names_list(mapping)
    
    with open(args.class_names, 'w', encoding='utf-8') as f:
        for name in class_names:
            f.write(f"{name}\n")
    
    print(f"✓ Created class names: {args.class_names}")
    print(f"  Total classes: {len(class_names)}")


if __name__ == '__main__':
    main()
