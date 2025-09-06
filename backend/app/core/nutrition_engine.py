"""Rule-based nutrition analysis engine."""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class FoodClass(Enum):
    """Nigerian food classification system."""
    CARBOHYDRATES = "carbohydrates"
    PROTEINS = "proteins"
    FATS = "fats"
    VITAMINS = "vitamins"
    MINERALS = "minerals"
    WATER = "water"


class RuleOperator(Enum):
    """Rule evaluation operators."""
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"


@dataclass
class NutritionProfile:
    """Nutrition profile for a meal."""
    carbohydrates: float = 0.0
    proteins: float = 0.0
    fats: float = 0.0
    vitamins: float = 0.0
    minerals: float = 0.0
    water: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "carbohydrates": self.carbohydrates,
            "proteins": self.proteins,
            "fats": self.fats,
            "vitamins": self.vitamins,
            "minerals": self.minerals,
            "water": self.water
        }

    def get_missing_groups(self, threshold: float = 0.1) -> List[str]:
        """Get food groups below threshold."""
        return [
            group for group, value in self.to_dict().items()
            if value < threshold
        ]

    def calculate_balance_score(self) -> float:
        """Calculate overall nutritional balance score."""
        values = list(self.to_dict().values())
        if not values:
            return 0.0

        # Calculate coefficient of variation (lower is more balanced)
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0

        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        cv = (variance ** 0.5) / mean_val

        # Convert to balance score (0-1, higher is better)
        return max(0.0, 1.0 - cv)


@dataclass
class NutritionRule:
    """Nutrition rule definition."""
    rule_id: str
    name: str
    conditions: List[Dict[str, Any]]
    feedback_template: str
    priority: int = 1
    is_active: bool = True

    def evaluate(self, profile: NutritionProfile, detected_foods: List[Dict[str, Any]]) -> bool:
        """Evaluate rule against nutrition profile and detected foods."""
        if not self.is_active:
            return False

        for condition in self.conditions:
            if not self._evaluate_condition(condition, profile, detected_foods):
                return False
        return True

    def _evaluate_condition(self, condition: Dict[str, Any],
                            profile: NutritionProfile,
                            detected_foods: List[Dict[str, Any]]) -> bool:
        """Evaluate a single condition."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not all([field, operator, value is not None]):
            return False

        # Get actual value based on field
        actual_value = self._get_field_value(field, profile, detected_foods)

        # Evaluate based on operator
        return self._apply_operator(actual_value, operator, value)

    def _get_field_value(self, field: str, profile: NutritionProfile,
                         detected_foods: List[Dict[str, Any]]) -> Any:
        """Get field value from profile or detected foods."""
        # Nutrition profile fields
        if hasattr(profile, field):
            return getattr(profile, field)

        # Special computed fields
        if field == "balance_score":
            return profile.calculate_balance_score()
        elif field == "missing_groups_count":
            return len(profile.get_missing_groups())
        elif field == "detected_food_count":
            return len(detected_foods)
        elif field == "detected_food_names":
            return [food.get("food_name", "") for food in detected_foods]
        elif field == "food_classes":
            return [food.get("food_class", "") for food in detected_foods]

        return None

    def _apply_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """Apply comparison operator."""
        try:
            if operator == RuleOperator.GREATER_THAN.value:
                return actual > expected
            elif operator == RuleOperator.LESS_THAN.value:
                return actual < expected
            elif operator == RuleOperator.EQUAL.value:
                return actual == expected
            elif operator == RuleOperator.GREATER_EQUAL.value:
                return actual >= expected
            elif operator == RuleOperator.LESS_EQUAL.value:
                return actual <= expected
            elif operator == RuleOperator.IN.value:
                return actual in expected
            elif operator == RuleOperator.NOT_IN.value:
                return actual not in expected
            elif operator == RuleOperator.CONTAINS.value:
                if isinstance(actual, list) and isinstance(expected, str):
                    # Check if any item in the list contains the expected string
                    return any(expected in str(item) for item in actual)
                elif isinstance(actual, str) and isinstance(expected, str):
                    return expected in actual
            return False
        except (TypeError, ValueError):
            return False


class NutritionAnalysisEngine:
    """Rule-based nutrition analysis engine."""

    def __init__(self):
        self.rules: List[NutritionRule] = []
        self.food_class_mapping = self._initialize_food_mapping()

    def _initialize_food_mapping(self) -> Dict[str, str]:
        """Initialize Nigerian food to class mapping."""
        return {
            # Carbohydrates
            "jollof_rice": FoodClass.CARBOHYDRATES.value,
            "white_rice": FoodClass.CARBOHYDRATES.value,
            "fried_rice": FoodClass.CARBOHYDRATES.value,
            "amala": FoodClass.CARBOHYDRATES.value,
            "fufu": FoodClass.CARBOHYDRATES.value,
            "pounded_yam": FoodClass.CARBOHYDRATES.value,
            "eba": FoodClass.CARBOHYDRATES.value,
            "tuwo": FoodClass.CARBOHYDRATES.value,
            "bread": FoodClass.CARBOHYDRATES.value,
            "yam": FoodClass.CARBOHYDRATES.value,
            "plantain": FoodClass.CARBOHYDRATES.value,
            "sweet_potato": FoodClass.CARBOHYDRATES.value,

            # Proteins
            "chicken": FoodClass.PROTEINS.value,
            "beef": FoodClass.PROTEINS.value,
            "fish": FoodClass.PROTEINS.value,
            "goat_meat": FoodClass.PROTEINS.value,
            "turkey": FoodClass.PROTEINS.value,
            "beans": FoodClass.PROTEINS.value,
            "moimoi": FoodClass.PROTEINS.value,
            "akara": FoodClass.PROTEINS.value,
            "egg": FoodClass.PROTEINS.value,
            "suya": FoodClass.PROTEINS.value,
            "kilishi": FoodClass.PROTEINS.value,

            # Fats/Oils
            "palm_oil": FoodClass.FATS.value,
            "groundnut_oil": FoodClass.FATS.value,
            "coconut": FoodClass.FATS.value,
            "groundnut": FoodClass.FATS.value,
            "avocado": FoodClass.FATS.value,

            # Vitamins (Fruits and some vegetables)
            "orange": FoodClass.VITAMINS.value,
            "banana": FoodClass.VITAMINS.value,
            "pineapple": FoodClass.VITAMINS.value,
            "mango": FoodClass.VITAMINS.value,
            "pawpaw": FoodClass.VITAMINS.value,
            "watermelon": FoodClass.VITAMINS.value,
            "tomato": FoodClass.VITAMINS.value,
            "pepper": FoodClass.VITAMINS.value,

            # Minerals (Vegetables and leafy greens)
            "efo_riro": FoodClass.MINERALS.value,
            "okra": FoodClass.MINERALS.value,
            "spinach": FoodClass.MINERALS.value,
            "ugwu": FoodClass.MINERALS.value,
            "bitter_leaf": FoodClass.MINERALS.value,
            "vegetable_soup": FoodClass.MINERALS.value,
            "egusi": FoodClass.MINERALS.value,
            "ogbono": FoodClass.MINERALS.value,

            # Water (Beverages and water-rich foods)
            "water": FoodClass.WATER.value,
            "zobo": FoodClass.WATER.value,
            "kunu": FoodClass.WATER.value,
            "palm_wine": FoodClass.WATER.value,
            "coconut_water": FoodClass.WATER.value,
        }

    def add_rule(self, rule: NutritionRule) -> None:
        """Add a nutrition rule to the engine."""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        return len(self.rules) < initial_count

    def update_rule(self, rule_id: str, updated_rule: NutritionRule) -> bool:
        """Update an existing rule."""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                self.rules[i] = updated_rule
                self.rules.sort(key=lambda r: r.priority, reverse=True)
                return True
        return False

    def get_rule(self, rule_id: str) -> Optional[NutritionRule]:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def classify_foods(self, detected_foods: List[Dict[str, Any]]) -> NutritionProfile:
        """Classify detected foods into nutrition profile."""
        profile = NutritionProfile()

        for food in detected_foods:
            food_name = food.get("food_name", "").lower()
            confidence = food.get("confidence", 0.0)

            # Get food class from mapping or use provided class
            food_class = self.food_class_mapping.get(
                food_name,
                food.get("food_class", "")
            )

            # Add to appropriate category
            if food_class == FoodClass.CARBOHYDRATES.value:
                profile.carbohydrates += confidence
            elif food_class == FoodClass.PROTEINS.value:
                profile.proteins += confidence
            elif food_class == FoodClass.FATS.value:
                profile.fats += confidence
            elif food_class == FoodClass.VITAMINS.value:
                profile.vitamins += confidence
            elif food_class == FoodClass.MINERALS.value:
                profile.minerals += confidence
            elif food_class == FoodClass.WATER.value:
                profile.water += confidence

        # Normalize values (optional - depends on requirements)
        total = sum(profile.to_dict().values())
        if total > 0:
            profile.carbohydrates /= total
            profile.proteins /= total
            profile.fats /= total
            profile.vitamins /= total
            profile.minerals /= total
            profile.water /= total

        return profile

    def evaluate_rules(self, profile: NutritionProfile,
                       detected_foods: List[Dict[str, Any]]) -> List[NutritionRule]:
        """Evaluate all rules and return matching ones."""
        matching_rules = []

        for rule in self.rules:
            try:
                if rule.evaluate(profile, detected_foods):
                    matching_rules.append(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")

        return matching_rules

    def analyze_nutrition(self, detected_foods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform complete nutrition analysis."""
        # Classify foods into nutrition profile
        profile = self.classify_foods(detected_foods)

        # Evaluate rules
        matching_rules = self.evaluate_rules(profile, detected_foods)

        # Generate analysis results
        return {
            "nutrition_profile": profile.to_dict(),
            "balance_score": profile.calculate_balance_score(),
            "missing_food_groups": profile.get_missing_groups(),
            "matching_rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "feedback_template": rule.feedback_template,
                    "priority": rule.priority
                }
                for rule in matching_rules
            ],
            "detected_food_count": len(detected_foods),
            "food_classes_present": list(set(
                self.food_class_mapping.get(
                    food.get("food_name", "").lower(), "unknown")
                for food in detected_foods
            ))
        }


# Global engine instance
nutrition_engine = NutritionAnalysisEngine()
