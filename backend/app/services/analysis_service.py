"""Food analysis and recognition service."""

from typing import List, Dict, Any
from uuid import UUID
import logging

from app.models.meal import FoodDetectionResult
from app.core.nutrition_engine import nutrition_engine

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for food recognition and nutritional analysis."""

    def __init__(self):
        # AI model will be loaded here in future tasks
        self.model = None
        self.nutrition_engine = nutrition_engine

    async def analyze_food(self, image_path: str) -> List[FoodDetectionResult]:
        """Analyze food items in image using AI model."""
        # Placeholder implementation - will be replaced with actual AI model
        # This simulates the food recognition process

        mock_detections = [
            FoodDetectionResult(
                food_name="jollof_rice",
                confidence=0.95,
                food_class="carbohydrates",
                bounding_box={"x": 0.1, "y": 0.1, "width": 0.4, "height": 0.4}
            ),
            FoodDetectionResult(
                food_name="chicken",
                confidence=0.88,
                food_class="proteins",
                bounding_box={"x": 0.5, "y": 0.2, "width": 0.3, "height": 0.3}
            )
        ]

        return mock_detections

    def classify_nutrition(self, detected_foods: List[FoodDetectionResult]) -> Dict[str, Any]:
        """Classify detected foods into nutritional categories using rule engine."""
        # Convert FoodDetectionResult objects to dictionaries
        foods_dict = [
            {
                "food_name": food.food_name,
                "confidence": food.confidence,
                "food_class": food.food_class,
                "bounding_box": food.bounding_box
            }
            for food in detected_foods
        ]

        # Use nutrition engine for classification
        profile = self.nutrition_engine.classify_foods(foods_dict)
        return profile.to_dict()

    def generate_insights(self, nutrition_profile: Dict[str, float]) -> Dict[str, Any]:
        """Generate nutritional insights from analysis."""
        # Create a simple profile object for compatibility
        from app.core.nutrition_engine import NutritionProfile

        profile = NutritionProfile(
            carbohydrates=nutrition_profile.get("carbohydrates", 0.0),
            proteins=nutrition_profile.get("proteins", 0.0),
            fats=nutrition_profile.get("fats", 0.0),
            vitamins=nutrition_profile.get("vitamins", 0.0),
            minerals=nutrition_profile.get("minerals", 0.0),
            water=nutrition_profile.get("water", 0.0)
        )

        return {
            "missing_food_groups": profile.get_missing_groups(),
            "balance_score": profile.calculate_balance_score(),
            "nutrition_distribution": nutrition_profile
        }

    async def analyze_nutrition_with_rules(self, detected_foods: List[FoodDetectionResult]) -> Dict[str, Any]:
        """Perform complete nutrition analysis using rule engine."""
        try:
            # Convert to dictionary format
            foods_dict = [
                {
                    "food_name": food.food_name,
                    "confidence": food.confidence,
                    "food_class": food.food_class,
                    "bounding_box": food.bounding_box
                }
                for food in detected_foods
            ]

            # Use nutrition engine for complete analysis
            analysis_result = self.nutrition_engine.analyze_nutrition(
                foods_dict)

            return analysis_result

        except Exception as e:
            logger.error(f"Error in nutrition analysis: {e}")
            # Fallback to basic analysis
            nutrition_profile = self.classify_nutrition(detected_foods)
            insights = self.generate_insights(nutrition_profile)

            return {
                "nutrition_profile": nutrition_profile,
                "balance_score": insights["balance_score"],
                "missing_food_groups": insights["missing_food_groups"],
                "matching_rules": [],
                "detected_food_count": len(detected_foods),
                "food_classes_present": list(set(food.food_class for food in detected_foods))
            }


analysis_service = AnalysisService()
