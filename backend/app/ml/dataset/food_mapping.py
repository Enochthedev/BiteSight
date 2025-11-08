"""
Food class mapping utilities for Nigerian food recognition.
Handles mapping between food items, nutritional categories, and model classes.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NutritionalCategory(Enum):
    """Enumeration of the six major nutritional categories."""
    CARBOHYDRATES = "carbohydrates"
    PROTEINS = "proteins"
    FATS_OILS = "fats_oils"
    VITAMINS = "vitamins"
    MINERALS = "minerals"
    WATER = "water"


@dataclass
class FoodClassInfo:
    """Information about a food class."""
    name: str
    local_names: List[str]
    nutritional_category: NutritionalCategory
    cultural_context: Optional[str] = None
    common_preparations: List[str] = None
    typical_ingredients: List[str] = None


class NigerianFoodMapper:
    """Utility class for mapping Nigerian foods to nutritional categories."""

    def __init__(self, metadata_path: Optional[Path] = None):
        """
        Initialize food mapper.

        Args:
            metadata_path: Path to Nigerian foods metadata file
        """
        self.food_classes: Dict[str, FoodClassInfo] = {}
        self.name_to_class: Dict[str, str] = {}
        self.nutritional_mapping: Dict[str, NutritionalCategory] = {}

        if metadata_path:
            self.load_from_metadata(metadata_path)
        else:
            self._initialize_default_mappings()

    def _initialize_default_mappings(self):
        """Initialize with default Nigerian food mappings."""
        default_foods = [
            # Carbohydrates
            FoodClassInfo(
                name="jollof_rice",
                local_names=["jollof", "party rice"],
                nutritional_category=NutritionalCategory.CARBOHYDRATES,
                cultural_context="Popular Nigerian rice dish cooked in tomato sauce",
                common_preparations=["party style",
                                     "smoky", "with vegetables"],
                typical_ingredients=["rice", "tomatoes", "onions", "spices"]
            ),
            FoodClassInfo(
                name="amala",
                local_names=["àmàlà", "yam flour"],
                nutritional_category=NutritionalCategory.CARBOHYDRATES,
                cultural_context="Traditional Yoruba swallow made from yam flour",
                common_preparations=["smooth", "with soup"],
                typical_ingredients=["yam flour", "water"]
            ),
            FoodClassInfo(
                name="pounded_yam",
                local_names=["iyan", "pounded yam"],
                nutritional_category=NutritionalCategory.CARBOHYDRATES,
                cultural_context="Traditional Nigerian swallow made from yam",
                common_preparations=["smooth", "stretchy"],
                typical_ingredients=["yam", "water"]
            ),
            FoodClassInfo(
                name="eba",
                local_names=["garri", "cassava flakes"],
                nutritional_category=NutritionalCategory.CARBOHYDRATES,
                cultural_context="Popular swallow made from cassava flakes",
                common_preparations=["thick", "smooth"],
                typical_ingredients=["garri", "hot water"]
            ),
            FoodClassInfo(
                name="fufu",
                local_names=["akpu", "cassava fufu"],
                nutritional_category=NutritionalCategory.CARBOHYDRATES,
                cultural_context="Traditional swallow made from cassava",
                common_preparations=["fermented", "smooth"],
                typical_ingredients=["cassava", "water"]
            ),

            # Proteins
            FoodClassInfo(
                name="beans",
                local_names=["ewa", "black-eyed peas"],
                nutritional_category=NutritionalCategory.PROTEINS,
                cultural_context="Common protein source in Nigerian cuisine",
                common_preparations=["stewed", "fried", "porridge"],
                typical_ingredients=["beans", "palm oil", "onions", "pepper"]
            ),
            FoodClassInfo(
                name="moimoi",
                local_names=["moin moin", "bean pudding"],
                nutritional_category=NutritionalCategory.PROTEINS,
                cultural_context="Steamed bean pudding, popular protein dish",
                common_preparations=["steamed", "with fish", "with eggs"],
                typical_ingredients=["beans", "pepper", "onions", "oil"]
            ),
            FoodClassInfo(
                name="suya",
                local_names=["tsire", "grilled meat"],
                nutritional_category=NutritionalCategory.PROTEINS,
                cultural_context="Popular grilled meat snack from Northern Nigeria",
                common_preparations=["spiced", "grilled", "skewered"],
                typical_ingredients=["beef", "suya spice", "onions"]
            ),
            FoodClassInfo(
                name="fish",
                local_names=["eja", "dried fish", "fresh fish"],
                nutritional_category=NutritionalCategory.PROTEINS,
                cultural_context="Important protein source in Nigerian meals",
                common_preparations=["fried", "grilled", "in stew"],
                typical_ingredients=["fish", "seasoning", "oil"]
            ),
            FoodClassInfo(
                name="chicken",
                local_names=["adiye", "fowl"],
                nutritional_category=NutritionalCategory.PROTEINS,
                cultural_context="Common protein in Nigerian households",
                common_preparations=["fried", "grilled", "in stew"],
                typical_ingredients=["chicken", "seasoning", "oil"]
            ),

            # Vitamins (Vegetables and Fruits)
            FoodClassInfo(
                name="efo_riro",
                local_names=["spinach stew", "vegetable soup"],
                nutritional_category=NutritionalCategory.VITAMINS,
                cultural_context="Popular Yoruba vegetable soup rich in vitamins",
                common_preparations=["with meat", "with fish", "spicy"],
                typical_ingredients=["spinach", "palm oil", "meat", "pepper"]
            ),
            FoodClassInfo(
                name="okra_soup",
                local_names=["okro", "lady fingers"],
                nutritional_category=NutritionalCategory.VITAMINS,
                cultural_context="Traditional soup rich in vitamins and minerals",
                common_preparations=["with meat", "with fish", "thick"],
                typical_ingredients=["okra", "palm oil", "meat", "seasoning"]
            ),
            FoodClassInfo(
                name="plantain",
                local_names=["ogede", "dodo"],
                nutritional_category=NutritionalCategory.VITAMINS,
                cultural_context="Popular fruit vegetable, source of vitamins",
                common_preparations=["fried", "boiled", "roasted"],
                typical_ingredients=["plantain", "oil"]
            ),

            # Fats and Oils
            FoodClassInfo(
                name="palm_oil_dishes",
                local_names=["epo pupa", "red oil"],
                nutritional_category=NutritionalCategory.FATS_OILS,
                cultural_context="Traditional cooking oil in Nigerian cuisine",
                common_preparations=["in stews", "for frying"],
                typical_ingredients=["palm oil"]
            )
        ]

        for food_info in default_foods:
            self.add_food_class(food_info)

    def add_food_class(self, food_info: FoodClassInfo):
        """Add a food class to the mapping."""
        self.food_classes[food_info.name] = food_info

        # Map all names (primary and local) to the class
        self.name_to_class[food_info.name] = food_info.name
        for local_name in food_info.local_names:
            self.name_to_class[local_name.lower()] = food_info.name

        # Map to nutritional category
        self.nutritional_mapping[food_info.name] = food_info.nutritional_category

    def load_from_metadata(self, metadata_path: Path):
        """Load food mappings from metadata file."""
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Handle both old and new JSON formats
            foods_dict = metadata.get('foods', {})
            
            # If foods is a dict (new format from our CSV)
            if isinstance(foods_dict, dict):
                for food_id, food_data in foods_dict.items():
                    try:
                        # Map category names
                        category_name = food_data.get('category', '').lower()
                        
                        # Handle category name variations
                        category_map = {
                            'carbohydrates': 'carbohydrates',
                            'protein': 'proteins',
                            'proteins': 'proteins',
                            'fats_oils': 'fats_oils',
                            'fats_and_oils': 'fats_oils',
                            'vitamins': 'vitamins',
                            'minerals': 'minerals',
                            'water': 'water',
                            'snacks': 'carbohydrates'  # Map snacks to carbs for now
                        }
                        
                        category_name = category_map.get(category_name, 'carbohydrates')
                        nutritional_cat = NutritionalCategory(category_name)

                        food_info = FoodClassInfo(
                            name=food_id,
                            local_names=food_data.get('local_names', {}).values() if isinstance(food_data.get('local_names'), dict) else [],
                            nutritional_category=nutritional_cat,
                            cultural_context=food_data.get('description', ''),
                            common_preparations=[food_data.get('preparation_method', '')],
                            typical_ingredients=[]
                        )

                        self.add_food_class(food_info)

                    except (KeyError, ValueError) as e:
                        logger.warning(f"Skipping invalid food entry {food_id}: {e}")
            
            # If foods is a list (old format)
            elif isinstance(foods_dict, list):
                for food_data in foods_dict:
                    try:
                        nutritional_cat = NutritionalCategory(
                            food_data['nutritional_category'])

                        food_info = FoodClassInfo(
                            name=food_data['name'],
                            local_names=food_data.get('local_names', []),
                            nutritional_category=nutritional_cat,
                            cultural_context=food_data.get('cultural_context'),
                            common_preparations=food_data.get(
                                'common_preparations', []),
                            typical_ingredients=food_data.get(
                                'typical_ingredients', [])
                        )

                        self.add_food_class(food_info)

                    except (KeyError, ValueError) as e:
                        logger.warning(f"Skipping invalid food entry: {e}")

            logger.info(
                f"Loaded {len(self.food_classes)} food classes from metadata")

        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            logger.exception(e)
            self._initialize_default_mappings()

    def get_food_class(self, food_name: str) -> Optional[FoodClassInfo]:
        """Get food class information by name."""
        normalized_name = food_name.lower().strip()
        class_name = self.name_to_class.get(normalized_name)
        if class_name:
            return self.food_classes.get(class_name)
        return None

    def get_nutritional_category(self, food_name: str) -> Optional[NutritionalCategory]:
        """Get nutritional category for a food item."""
        food_class = self.get_food_class(food_name)
        return food_class.nutritional_category if food_class else None

    def get_all_classes(self) -> List[str]:
        """Get list of all food class names."""
        return list(self.food_classes.keys())

    def get_classes_by_category(self, category: NutritionalCategory) -> List[str]:
        """Get all food classes in a specific nutritional category."""
        return [
            name for name, info in self.food_classes.items()
            if info.nutritional_category == category
        ]

    def create_model_class_mapping(self) -> Dict[int, str]:
        """Create mapping from model class indices to food class names."""
        class_names = sorted(self.get_all_classes())
        return {i: name for i, name in enumerate(class_names)}

    def create_reverse_model_mapping(self) -> Dict[str, int]:
        """Create mapping from food class names to model class indices."""
        class_names = sorted(self.get_all_classes())
        return {name: i for i, name in enumerate(class_names)}

    def analyze_meal_nutrition(self, detected_foods: List[Tuple[str, float]]) -> Dict[str, any]:
        """
        Analyze nutritional balance of detected foods.

        Args:
            detected_foods: List of (food_name, confidence) tuples

        Returns:
            Dictionary with nutritional analysis
        """
        category_counts = {cat: 0 for cat in NutritionalCategory}
        detected_categories = set()
        food_details = []

        for food_name, confidence in detected_foods:
            food_info = self.get_food_class(food_name)
            if food_info:
                category_counts[food_info.nutritional_category] += 1
                detected_categories.add(food_info.nutritional_category)
                food_details.append({
                    'name': food_name,
                    'confidence': confidence,
                    'category': food_info.nutritional_category.value,
                    'local_names': food_info.local_names
                })

        # Identify missing categories
        missing_categories = [
            cat.value for cat in NutritionalCategory
            if cat not in detected_categories
        ]

        # Calculate balance score (0-1)
        balance_score = len(detected_categories) / len(NutritionalCategory)

        return {
            'detected_foods': food_details,
            'category_distribution': {cat.value: count for cat, count in category_counts.items()},
            'missing_categories': missing_categories,
            'balance_score': balance_score,
            'total_foods_detected': len(detected_foods)
        }

    def get_recommendations_for_missing_categories(
        self,
        missing_categories: List[str]
    ) -> Dict[str, List[str]]:
        """
        Get food recommendations for missing nutritional categories.

        Args:
            missing_categories: List of missing category names

        Returns:
            Dictionary mapping categories to recommended foods
        """
        recommendations = {}

        for category_name in missing_categories:
            try:
                category = NutritionalCategory(category_name)
                recommended_foods = self.get_classes_by_category(category)

                # Get user-friendly names with local alternatives
                food_suggestions = []
                for food_name in recommended_foods[:3]:  # Limit to top 3
                    food_info = self.food_classes[food_name]
                    suggestion = food_info.name.replace('_', ' ').title()
                    if food_info.local_names:
                        suggestion += f" ({food_info.local_names[0]})"
                    food_suggestions.append(suggestion)

                recommendations[category_name] = food_suggestions

            except ValueError:
                logger.warning(
                    f"Unknown nutritional category: {category_name}")

        return recommendations

    def export_mappings(self, output_path: Path):
        """Export all mappings to JSON file."""
        export_data = {
            'food_classes': {},
            'nutritional_categories': [cat.value for cat in NutritionalCategory],
            'model_class_mapping': self.create_model_class_mapping()
        }

        for name, info in self.food_classes.items():
            export_data['food_classes'][name] = {
                'local_names': info.local_names,
                'nutritional_category': info.nutritional_category.value,
                'cultural_context': info.cultural_context,
                'common_preparations': info.common_preparations or [],
                'typical_ingredients': info.typical_ingredients or []
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Food mappings exported to {output_path}")


def create_sample_metadata_file(output_path: Path):
    """Create a sample metadata file with Nigerian foods."""
    sample_data = {
        "dataset_info": {
            "name": "Nigerian Food Recognition Dataset",
            "version": "1.0",
            "description": "Dataset of common Nigerian foods for nutritional analysis"
        },
        "foods": [
            {
                "name": "jollof_rice",
                "local_names": ["jollof", "party rice"],
                "food_class": "jollof_rice",
                "nutritional_category": "carbohydrates",
                "cultural_context": "Popular Nigerian rice dish cooked in tomato sauce",
                "common_preparations": ["party style", "smoky", "with vegetables"],
                "typical_ingredients": ["rice", "tomatoes", "onions", "spices"]
            },
            {
                "name": "amala",
                "local_names": ["àmàlà", "yam flour"],
                "food_class": "amala",
                "nutritional_category": "carbohydrates",
                "cultural_context": "Traditional Yoruba swallow made from yam flour"
            },
            {
                "name": "beans",
                "local_names": ["ewa", "black-eyed peas"],
                "food_class": "beans",
                "nutritional_category": "proteins",
                "cultural_context": "Common protein source in Nigerian cuisine"
            },
            {
                "name": "moimoi",
                "local_names": ["moin moin", "bean pudding"],
                "food_class": "moimoi",
                "nutritional_category": "proteins",
                "cultural_context": "Steamed bean pudding, popular protein dish"
            },
            {
                "name": "efo_riro",
                "local_names": ["spinach stew", "vegetable soup"],
                "food_class": "efo_riro",
                "nutritional_category": "vitamins",
                "cultural_context": "Popular Yoruba vegetable soup rich in vitamins"
            }
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Sample metadata file created at {output_path}")
