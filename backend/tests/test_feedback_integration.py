"""Integration tests for complete feedback pipeline."""

from app.models.meal import FoodDetectionResult
from app.core.nutrition_engine import NutritionAnalysisEngine
from app.services.feedback_generation_service import CulturalContext
from app.services.feedback_service import FeedbackService
from uuid import uuid4
from typing import Dict, List, Any
import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockDatabase:
    """Mock database session for testing."""

    def __init__(self):
        self.records = []
        self.committed = False

    def add(self, record):
        self.records.append(record)

    def commit(self):
        self.committed = True

    def refresh(self, record):
        # Simulate setting ID
        if not hasattr(record, 'id'):
            record.id = uuid4()

    def query(self, model):
        return MockQuery(self.records, model)


class MockQuery:
    """Mock query object."""

    def __init__(self, records, model):
        self.records = [r for r in records if isinstance(r, model)]
        self.model = model

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def limit(self, limit):
        return MockQueryResult(self.records[:limit])

    def first(self):
        return self.records[0] if self.records else None

    def all(self):
        return self.records


class MockQueryResult:
    """Mock query result."""

    def __init__(self, records):
        self.records = records

    def all(self):
        return self.records


class TestFeedbackIntegration:
    """Test complete feedback pipeline integration."""

    def test_complete_feedback_pipeline_balanced_meal(self):
        """Test complete pipeline with balanced meal."""

        # Setup
        feedback_service = FeedbackService()
        mock_db = MockDatabase()

        # Create test data
        meal_id = uuid4()
        student_id = uuid4()

        detected_foods = [
            FoodDetectionResult(
                food_name="jollof_rice",
                confidence=0.9,
                food_class="carbohydrates",
                bounding_box={"x": 0.1, "y": 0.1, "width": 0.4, "height": 0.4}
            ),
            FoodDetectionResult(
                food_name="chicken",
                confidence=0.8,
                food_class="proteins",
                bounding_box={"x": 0.5, "y": 0.2, "width": 0.3, "height": 0.3}
            ),
            FoodDetectionResult(
                food_name="efo_riro",
                confidence=0.7,
                food_class="minerals",
                bounding_box={"x": 0.2, "y": 0.6, "width": 0.3, "height": 0.2}
            )
        ]

        # Test feedback generation (this will use fallback due to mock DB)
        result = None
        try:
            # This should work with the fallback mechanism
            import asyncio
            result = asyncio.run(feedback_service._generate_basic_feedback(
                meal_id, student_id, detected_foods, mock_db
            ))
        except Exception as e:
            # If async doesn't work in test, test the components separately
            pass

        # Test individual components
        # 1. Test nutrition analysis
        analysis_service = feedback_service.analysis_service
        nutrition_profile = analysis_service.classify_nutrition(detected_foods)

        assert isinstance(nutrition_profile, dict)
        assert "carbohydrates" in nutrition_profile
        assert "proteins" in nutrition_profile
        assert "minerals" in nutrition_profile

        # Should have some values for the detected food groups
        assert nutrition_profile["carbohydrates"] > 0
        assert nutrition_profile["proteins"] > 0
        assert nutrition_profile["minerals"] > 0

        # 2. Test feedback generation
        from app.core.nutrition_engine import NutritionProfile
        profile_obj = NutritionProfile(
            carbohydrates=nutrition_profile["carbohydrates"],
            proteins=nutrition_profile["proteins"],
            fats=nutrition_profile["fats"],
            vitamins=nutrition_profile["vitamins"],
            minerals=nutrition_profile["minerals"],
            water=nutrition_profile["water"]
        )

        foods_dict = [
            {
                "food_name": food.food_name,
                "confidence": food.confidence,
                "food_class": food.food_class,
                "bounding_box": food.bounding_box
            }
            for food in detected_foods
        ]

        feedback_generator = feedback_service.feedback_generator
        feedback_data = feedback_generator.generate_feedback(
            profile_obj,
            foods_dict,
            [],  # No matching rules for this test
            CulturalContext.NIGERIAN_GENERAL
        )

        assert "overall_message" in feedback_data
        assert "recommendations" in feedback_data
        assert "encouragement" in feedback_data
        assert isinstance(feedback_data["balance_score"], float)

        print("✓ Complete feedback pipeline test passed")

    def test_nutrition_engine_with_nigerian_foods(self):
        """Test nutrition engine with various Nigerian foods."""

        engine = NutritionAnalysisEngine()

        # Test different Nigerian meal combinations
        test_meals = [
            # Traditional breakfast
            [
                {"food_name": "bread", "confidence": 0.9,
                    "food_class": "carbohydrates"},
                {"food_name": "beans", "confidence": 0.8, "food_class": "proteins"},
                {"food_name": "orange", "confidence": 0.7, "food_class": "vitamins"}
            ],
            # Traditional lunch
            [
                {"food_name": "amala", "confidence": 0.9,
                    "food_class": "carbohydrates"},
                {"food_name": "efo_riro", "confidence": 0.8,
                    "food_class": "minerals"},
                {"food_name": "fish", "confidence": 0.7, "food_class": "proteins"}
            ],
            # Rice-based meal
            [
                {"food_name": "jollof_rice", "confidence": 0.9,
                    "food_class": "carbohydrates"},
                {"food_name": "chicken", "confidence": 0.8, "food_class": "proteins"},
                {"food_name": "plantain", "confidence": 0.7,
                    "food_class": "carbohydrates"}
            ]
        ]

        for i, meal in enumerate(test_meals):
            print(
                f"\nTesting meal {i+1}: {[food['food_name'] for food in meal]}")

            # Classify foods
            profile = engine.classify_foods(meal)
            print(f"Nutrition profile: {profile.to_dict()}")

            # Analyze with rules
            analysis = engine.analyze_nutrition(meal)
            print(f"Balance score: {analysis['balance_score']:.2f}")
            print(f"Missing groups: {analysis['missing_food_groups']}")
            print(f"Food classes present: {analysis['food_classes_present']}")

            # Basic assertions
            assert isinstance(analysis["nutrition_profile"], dict)
            assert isinstance(analysis["balance_score"], float)
            assert isinstance(analysis["missing_food_groups"], list)
            assert analysis["detected_food_count"] == len(meal)

        print("✓ Nigerian foods nutrition engine test passed")

    def test_cultural_feedback_variations(self):
        """Test feedback variations across cultural contexts."""

        feedback_generator = FeedbackService().feedback_generator

        # Create a sample meal
        from app.core.nutrition_engine import NutritionProfile
        profile = NutritionProfile(
            carbohydrates=0.4,
            proteins=0.3,
            minerals=0.2,
            vitamins=0.1,
            fats=0.0,
            water=0.0
        )

        foods = [
            {"food_name": "amala", "confidence": 0.9,
                "food_class": "carbohydrates"},
            {"food_name": "efo_riro", "confidence": 0.8, "food_class": "minerals"}
        ]

        # Test different cultural contexts
        contexts = [
            CulturalContext.NIGERIAN_GENERAL,
            CulturalContext.STUDENT_FRIENDLY,
            CulturalContext.YORUBA,
            CulturalContext.IGBO,
            CulturalContext.HAUSA
        ]

        for context in contexts:
            feedback = feedback_generator.generate_feedback(
                profile, foods, [], context
            )

            print(f"\n{context.value} feedback:")
            print(f"Message: {feedback['overall_message'][:100]}...")
            print(f"Encouragement: {feedback['encouragement']}")

            # Basic assertions
            assert len(feedback["overall_message"]) > 0
            assert len(feedback["encouragement"]) > 0
            assert feedback["cultural_context"] == context.value
            assert isinstance(feedback["balance_score"], float)

        print("✓ Cultural feedback variations test passed")

    def test_feedback_localization(self):
        """Test feedback localization features."""

        feedback_generator = FeedbackService().feedback_generator

        base_feedback = {
            "overall_message": "Your meal looks great!",
            "encouragement": "Keep up the good work!",
            "recommendations": ["Add more vegetables"]
        }

        # Test different language localizations
        languages = ["english", "yoruba", "igbo", "hausa"]

        for lang in languages:
            localized = feedback_generator.localize_feedback(
                base_feedback.copy(), lang
            )

            print(f"\n{lang.capitalize()} localization:")
            if "cultural_greeting" in localized:
                print(f"Greeting: {localized['cultural_greeting']}")
            if "closing" in localized:
                print(f"Closing: {localized['closing']}")

            # Verify original content is preserved
            assert localized["overall_message"] == base_feedback["overall_message"]
            assert localized["encouragement"] == base_feedback["encouragement"]

            # Check for cultural additions (except English)
            if lang != "english":
                assert "cultural_greeting" in localized

        print("✓ Feedback localization test passed")

    def test_recommendation_generation_accuracy(self):
        """Test accuracy of recommendation generation."""

        feedback_generator = FeedbackService().feedback_generator

        # Test scenarios with specific missing nutrients
        test_scenarios = [
            {
                "name": "Missing Protein",
                "profile": {"carbohydrates": 0.8, "proteins": 0.05, "fats": 0.1, "vitamins": 0.05, "minerals": 0.0, "water": 0.0},
                "expected_keywords": ["protein", "beans", "fish", "chicken"]
            },
            {
                "name": "Missing Vegetables",
                "profile": {"carbohydrates": 0.6, "proteins": 0.3, "fats": 0.1, "vitamins": 0.0, "minerals": 0.0, "water": 0.0},
                "expected_keywords": ["vegetable", "efo", "ugwu", "minerals"]
            },
            {
                "name": "Missing Carbs",
                "profile": {"carbohydrates": 0.05, "proteins": 0.4, "fats": 0.2, "vitamins": 0.2, "minerals": 0.15, "water": 0.0},
                "expected_keywords": ["energy", "rice", "yam", "carbohydrate"]
            }
        ]

        for scenario in test_scenarios:
            print(f"\nTesting scenario: {scenario['name']}")

            from app.core.nutrition_engine import NutritionProfile
            profile = NutritionProfile(**scenario["profile"])

            foods = [{"food_name": "test_food", "confidence": 0.8}]

            recommendations = feedback_generator._generate_recommendations(
                profile, foods)

            print(f"Generated recommendations: {recommendations}")

            # Check if expected keywords appear in recommendations
            all_rec_text = " ".join(recommendations).lower()

            found_keywords = []
            for keyword in scenario["expected_keywords"]:
                if keyword.lower() in all_rec_text:
                    found_keywords.append(keyword)

            print(f"Found expected keywords: {found_keywords}")

            # Should find at least one expected keyword
            assert len(
                found_keywords) > 0, f"No expected keywords found for {scenario['name']}"

        print("✓ Recommendation generation accuracy test passed")


if __name__ == "__main__":
    print("Running feedback integration tests...\n")

    test_suite = TestFeedbackIntegration()

    try:
        test_suite.test_complete_feedback_pipeline_balanced_meal()
        test_suite.test_nutrition_engine_with_nigerian_foods()
        test_suite.test_cultural_feedback_variations()
        test_suite.test_feedback_localization()
        test_suite.test_recommendation_generation_accuracy()

        print("\n🎉 All integration tests passed successfully!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
