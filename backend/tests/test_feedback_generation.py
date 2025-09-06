"""Tests for feedback generation service."""

import pytest
from typing import Dict, List, Any

from app.services.feedback_generation_service import (
    NigerianFeedbackGenerator,
    FeedbackTemplate,
    FeedbackType,
    CulturalContext
)
from app.core.nutrition_engine import NutritionProfile, NutritionRule


class TestFeedbackTemplate:
    """Test feedback template functionality."""

    def test_template_creation(self):
        """Test creating feedback template."""
        template = FeedbackTemplate(
            template_id="test_template",
            message_template="Hello {name}! Your meal has {score}% balance.",
            feedback_type=FeedbackType.ENCOURAGEMENT,
            cultural_context=CulturalContext.NIGERIAN_GENERAL,
            food_examples=["rice", "beans"],
            priority=5
        )

        assert template.template_id == "test_template"
        assert template.feedback_type == FeedbackType.ENCOURAGEMENT
        assert template.cultural_context == CulturalContext.NIGERIAN_GENERAL
        assert "rice" in template.food_examples

    def test_template_formatting(self):
        """Test template message formatting."""
        template = FeedbackTemplate(
            template_id="test",
            message_template="Hello {name}! Your score is {score}%.",
            feedback_type=FeedbackType.ENCOURAGEMENT,
            cultural_context=CulturalContext.NIGERIAN_GENERAL,
            food_examples=[]
        )

        formatted = template.format_message(name="Student", score=85)
        assert formatted == "Hello Student! Your score is 85%."

    def test_template_missing_variable(self):
        """Test template with missing variable."""
        template = FeedbackTemplate(
            template_id="test",
            message_template="Hello {name}! Your score is {missing_var}%.",
            feedback_type=FeedbackType.ENCOURAGEMENT,
            cultural_context=CulturalContext.NIGERIAN_GENERAL,
            food_examples=[]
        )

        # Should return original template when variable is missing
        formatted = template.format_message(name="Student")
        assert "Hello {name}! Your score is {missing_var}%." in formatted


class TestNigerianFeedbackGenerator:
    """Test Nigerian feedback generator."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = NigerianFeedbackGenerator()

        assert len(generator.templates) > 0
        assert len(generator.food_suggestions) > 0
        assert len(generator.encouragement_phrases) > 0

        # Check that we have different types of templates
        template_types = [t.feedback_type for t in generator.templates]
        assert FeedbackType.CELEBRATION in template_types
        assert FeedbackType.SUGGESTION in template_types
        assert FeedbackType.EDUCATIONAL in template_types

    def test_food_suggestions_structure(self):
        """Test food suggestions structure."""
        generator = NigerianFeedbackGenerator()

        required_categories = ["proteins",
                               "vegetables", "carbohydrates", "fruits"]
        for category in required_categories:
            assert category in generator.food_suggestions
            assert len(generator.food_suggestions[category]) > 0

        # Check for Nigerian foods
        proteins = generator.food_suggestions["proteins"]
        assert any("beans" in food for food in proteins)
        assert any("moimoi" in food for food in proteins)

        vegetables = generator.food_suggestions["vegetables"]
        assert any("efo riro" in food for food in vegetables)
        assert any("ugwu" in food for food in vegetables)

    def test_generate_feedback_balanced_meal(self):
        """Test feedback generation for balanced meal."""
        generator = NigerianFeedbackGenerator()

        # Create a balanced nutrition profile
        balanced_profile = NutritionProfile(
            carbohydrates=0.25,
            proteins=0.25,
            fats=0.15,
            vitamins=0.15,
            minerals=0.15,
            water=0.05
        )

        detected_foods = [
            {"food_name": "jollof_rice", "confidence": 0.9},
            {"food_name": "chicken", "confidence": 0.8},
            {"food_name": "efo_riro", "confidence": 0.7}
        ]

        # Create a mock rule for well-balanced meal
        well_balanced_rule = NutritionRule(
            rule_id="well_balanced",
            name="Well Balanced",
            conditions=[],
            feedback_template="Great balance!",
            priority=10
        )

        feedback = generator.generate_feedback(
            balanced_profile,
            detected_foods,
            [well_balanced_rule]
        )

        assert "overall_message" in feedback
        assert "specific_feedback" in feedback
        assert "recommendations" in feedback
        assert "encouragement" in feedback
        assert feedback["balance_score"] > 0.5

        # Should have positive feedback for balanced meal
        assert len(feedback["specific_feedback"]) > 0

    def test_generate_feedback_missing_protein(self):
        """Test feedback generation for meal missing protein."""
        generator = NigerianFeedbackGenerator()

        # Create profile missing protein
        low_protein_profile = NutritionProfile(
            carbohydrates=0.8,
            proteins=0.05,  # Very low
            fats=0.1,
            vitamins=0.05,
            minerals=0.0,
            water=0.0
        )

        detected_foods = [
            {"food_name": "jollof_rice", "confidence": 0.9}
        ]

        # Create rule for missing protein
        missing_protein_rule = NutritionRule(
            rule_id="missing_protein",
            name="Missing Protein",
            conditions=[
                {"field": "proteins", "operator": "lt", "value": 0.1}
            ],
            feedback_template="Add protein!",
            priority=5
        )

        feedback = generator.generate_feedback(
            low_protein_profile,
            detected_foods,
            [missing_protein_rule]
        )

        # Should suggest protein additions
        recommendations = feedback["recommendations"]
        protein_mentioned = any("protein" in rec.lower()
                                for rec in recommendations)
        assert protein_mentioned or len(recommendations) > 0

        # Should have suggestions in feedback
        assert len(feedback["specific_feedback"]) > 0

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        generator = NigerianFeedbackGenerator()

        # Profile missing vegetables and proteins
        profile = NutritionProfile(
            carbohydrates=0.9,
            proteins=0.05,
            fats=0.05,
            vitamins=0.0,
            minerals=0.0,  # Missing vegetables
            water=0.0
        )

        detected_foods = [{"food_name": "rice", "confidence": 0.9}]

        recommendations = generator._generate_recommendations(
            profile, detected_foods)

        assert len(recommendations) > 0
        # Should suggest adding missing food groups
        rec_text = " ".join(recommendations).lower()
        assert "minerals" in rec_text or "vegetables" in rec_text or "proteins" in rec_text

    def test_encouragement_messages(self):
        """Test encouragement message generation."""
        generator = NigerianFeedbackGenerator()

        # Test with high balance score
        high_balance_profile = NutritionProfile(
            carbohydrates=0.2, proteins=0.2, fats=0.2,
            vitamins=0.2, minerals=0.2, water=0.0
        )

        encouragement = generator._get_encouragement_message(
            high_balance_profile, [])
        assert len(encouragement) > 0
        assert isinstance(encouragement, str)

        # Test with low balance score
        low_balance_profile = NutritionProfile(carbohydrates=1.0)

        encouragement = generator._get_encouragement_message(
            low_balance_profile, [])
        assert len(encouragement) > 0
        assert isinstance(encouragement, str)

    def test_cultural_context_templates(self):
        """Test templates for different cultural contexts."""
        generator = NigerianFeedbackGenerator()

        # Check that we have templates for different cultural contexts
        contexts = [t.cultural_context for t in generator.templates]
        assert CulturalContext.NIGERIAN_GENERAL in contexts
        assert CulturalContext.STUDENT_FRIENDLY in contexts

        # Check for regional templates
        regional_contexts = [CulturalContext.YORUBA,
                             CulturalContext.IGBO, CulturalContext.HAUSA]
        has_regional = any(ctx in contexts for ctx in regional_contexts)
        assert has_regional, "Should have at least one regional template"

    def test_localization(self):
        """Test feedback localization."""
        generator = NigerianFeedbackGenerator()

        base_feedback = {
            "overall_message": "Great meal!",
            "encouragement": "Keep it up!"
        }

        # Test Yoruba localization
        yoruba_feedback = generator.localize_feedback(base_feedback, "yoruba")
        assert "cultural_greeting" in yoruba_feedback
        assert "Ẹ ku" in yoruba_feedback["cultural_greeting"]

        # Test Igbo localization
        igbo_feedback = generator.localize_feedback(base_feedback, "igbo")
        assert "cultural_greeting" in igbo_feedback
        assert "Ndewo" in igbo_feedback["cultural_greeting"]

        # Test Hausa localization
        hausa_feedback = generator.localize_feedback(base_feedback, "hausa")
        assert "cultural_greeting" in hausa_feedback
        assert "Sannu" in hausa_feedback["cultural_greeting"]

    def test_nigerian_food_coverage(self):
        """Test that Nigerian foods are well covered in suggestions."""
        generator = NigerianFeedbackGenerator()

        # Check for key Nigerian foods in suggestions
        all_foods = []
        for category in generator.food_suggestions.values():
            all_foods.extend(category)

        nigerian_foods = [
            "beans", "moimoi", "akara", "efo riro", "ugwu", "amala",
            "fufu", "jollof rice", "suya", "kilishi"
        ]

        for food in nigerian_foods:
            found = any(food in suggestion.lower() for suggestion in all_foods)
            assert found, f"Nigerian food '{food}' not found in suggestions"

    def test_template_priority_system(self):
        """Test that templates have appropriate priorities."""
        generator = NigerianFeedbackGenerator()

        # Celebration templates should have high priority
        celebration_templates = [t for t in generator.templates
                                 if t.feedback_type == FeedbackType.CELEBRATION]
        assert len(celebration_templates) > 0

        for template in celebration_templates:
            assert template.priority >= 8, "Celebration templates should have high priority"

        # Warning templates should have lower priority
        warning_templates = [t for t in generator.templates
                             if t.feedback_type == FeedbackType.WARNING]

        for template in warning_templates:
            assert template.priority <= 5, "Warning templates should have lower priority"


if __name__ == "__main__":
    pytest.main([__file__])
