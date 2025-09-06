"""Tests for nutrition analysis engine."""

import pytest
from typing import Dict, List, Any

from app.core.nutrition_engine import (
    NutritionProfile,
    NutritionRule,
    NutritionAnalysisEngine,
    FoodClass,
    RuleOperator
)


class TestNutritionProfile:
    """Test nutrition profile functionality."""

    def test_nutrition_profile_creation(self):
        """Test creating nutrition profile."""
        profile = NutritionProfile(
            carbohydrates=0.4,
            proteins=0.3,
            fats=0.1,
            vitamins=0.1,
            minerals=0.1,
            water=0.0
        )

        assert profile.carbohydrates == 0.4
        assert profile.proteins == 0.3
        assert profile.fats == 0.1

    def test_to_dict(self):
        """Test converting profile to dictionary."""
        profile = NutritionProfile(carbohydrates=0.5, proteins=0.3)
        result = profile.to_dict()

        assert isinstance(result, dict)
        assert result["carbohydrates"] == 0.5
        assert result["proteins"] == 0.3
        assert result["fats"] == 0.0  # Default value

    def test_get_missing_groups(self):
        """Test identifying missing food groups."""
        profile = NutritionProfile(
            carbohydrates=0.5,
            proteins=0.3,
            fats=0.05,  # Below threshold
            vitamins=0.0,  # Missing
            minerals=0.15,
            water=0.0  # Missing
        )

        missing = profile.get_missing_groups(threshold=0.1)
        assert "fats" in missing
        assert "vitamins" in missing
        assert "water" in missing
        assert "carbohydrates" not in missing
        assert "proteins" not in missing
        assert "minerals" not in missing

    def test_calculate_balance_score(self):
        """Test balance score calculation."""
        # Perfectly balanced
        balanced_profile = NutritionProfile(
            carbohydrates=1/6, proteins=1/6, fats=1/6,
            vitamins=1/6, minerals=1/6, water=1/6
        )
        balanced_score = balanced_profile.calculate_balance_score()
        assert balanced_score > 0.9  # Should be close to 1

        # Unbalanced (only carbs)
        unbalanced_profile = NutritionProfile(carbohydrates=1.0)
        unbalanced_score = unbalanced_profile.calculate_balance_score()
        assert unbalanced_score < 0.5  # Should be low

        # Empty profile
        empty_profile = NutritionProfile()
        empty_score = empty_profile.calculate_balance_score()
        assert empty_score == 0.0


class TestNutritionRule:
    """Test nutrition rule functionality."""

    def test_rule_creation(self):
        """Test creating nutrition rule."""
        rule = NutritionRule(
            rule_id="test_rule",
            name="Test Rule",
            conditions=[{"field": "proteins", "operator": "lt", "value": 0.1}],
            feedback_template="Add more protein!",
            priority=5
        )

        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.priority == 5
        assert rule.is_active is True

    def test_rule_evaluation_simple(self):
        """Test simple rule evaluation."""
        rule = NutritionRule(
            rule_id="low_protein",
            name="Low Protein",
            conditions=[{"field": "proteins", "operator": "lt", "value": 0.1}],
            feedback_template="Add protein!"
        )

        # Profile with low protein
        low_protein_profile = NutritionProfile(proteins=0.05)
        assert rule.evaluate(low_protein_profile, []) is True

        # Profile with adequate protein
        good_protein_profile = NutritionProfile(proteins=0.3)
        assert rule.evaluate(good_protein_profile, []) is False

    def test_rule_evaluation_multiple_conditions(self):
        """Test rule with multiple conditions."""
        rule = NutritionRule(
            rule_id="well_balanced",
            name="Well Balanced",
            conditions=[
                {"field": "balance_score", "operator": "gte", "value": 0.5},
                {"field": "missing_groups_count", "operator": "lte", "value": 1}
            ],
            feedback_template="Great balance!"
        )

        # Balanced profile
        balanced_profile = NutritionProfile(
            carbohydrates=0.25, proteins=0.25, fats=0.15,
            vitamins=0.15, minerals=0.15, water=0.05
        )
        assert rule.evaluate(balanced_profile, []) is True

        # Unbalanced profile
        unbalanced_profile = NutritionProfile(carbohydrates=1.0)
        assert rule.evaluate(unbalanced_profile, []) is False

    def test_rule_evaluation_food_names(self):
        """Test rule evaluation with food names."""
        rule = NutritionRule(
            rule_id="rice_beans",
            name="Rice and Beans",
            conditions=[
                {"field": "detected_food_names",
                    "operator": "contains", "value": "rice"},
                {"field": "detected_food_names",
                    "operator": "contains", "value": "beans"}
            ],
            feedback_template="Great combo!"
        )

        foods_with_combo = [
            {"food_name": "jollof_rice", "confidence": 0.9},
            {"food_name": "beans", "confidence": 0.8}
        ]

        foods_without_combo = [
            {"food_name": "jollof_rice", "confidence": 0.9},
            {"food_name": "chicken", "confidence": 0.8}
        ]

        profile = NutritionProfile()
        assert rule.evaluate(profile, foods_with_combo) is True
        assert rule.evaluate(profile, foods_without_combo) is False

    def test_inactive_rule(self):
        """Test that inactive rules don't match."""
        rule = NutritionRule(
            rule_id="inactive",
            name="Inactive Rule",
            conditions=[{"field": "proteins", "operator": "lt", "value": 1.0}],
            feedback_template="This should not trigger",
            is_active=False
        )

        profile = NutritionProfile(proteins=0.0)
        assert rule.evaluate(profile, []) is False


class TestNutritionAnalysisEngine:
    """Test nutrition analysis engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = NutritionAnalysisEngine()
        assert len(engine.food_class_mapping) > 0
        assert "jollof_rice" in engine.food_class_mapping
        assert engine.food_class_mapping["jollof_rice"] == FoodClass.CARBOHYDRATES.value

    def test_add_remove_rule(self):
        """Test adding and removing rules."""
        engine = NutritionAnalysisEngine()
        initial_count = len(engine.rules)

        rule = NutritionRule(
            rule_id="test_rule",
            name="Test Rule",
            conditions=[{"field": "proteins", "operator": "lt", "value": 0.1}],
            feedback_template="Test feedback"
        )

        # Add rule
        engine.add_rule(rule)
        assert len(engine.rules) == initial_count + 1

        # Remove rule
        removed = engine.remove_rule("test_rule")
        assert removed is True
        assert len(engine.rules) == initial_count

        # Try to remove non-existent rule
        removed = engine.remove_rule("non_existent")
        assert removed is False

    def test_classify_foods(self):
        """Test food classification."""
        engine = NutritionAnalysisEngine()

        detected_foods = [
            {"food_name": "jollof_rice", "confidence": 0.9,
                "food_class": "carbohydrates"},
            {"food_name": "chicken", "confidence": 0.8, "food_class": "proteins"},
            {"food_name": "efo_riro", "confidence": 0.7, "food_class": "minerals"}
        ]

        profile = engine.classify_foods(detected_foods)

        assert profile.carbohydrates > 0
        assert profile.proteins > 0
        assert profile.minerals > 0
        assert profile.fats == 0  # No fats in the meal

    def test_evaluate_rules(self):
        """Test rule evaluation."""
        engine = NutritionAnalysisEngine()

        # Add a test rule
        rule = NutritionRule(
            rule_id="test_low_protein",
            name="Low Protein Test",
            conditions=[{"field": "proteins", "operator": "lt", "value": 0.1}],
            feedback_template="Need more protein!"
        )
        engine.add_rule(rule)

        # Profile with low protein
        low_protein_profile = NutritionProfile(
            carbohydrates=0.8, proteins=0.05)
        matching_rules = engine.evaluate_rules(low_protein_profile, [])

        rule_ids = [rule.rule_id for rule in matching_rules]
        assert "test_low_protein" in rule_ids

    def test_analyze_nutrition_complete(self):
        """Test complete nutrition analysis."""
        engine = NutritionAnalysisEngine()

        detected_foods = [
            {"food_name": "jollof_rice", "confidence": 0.9,
                "food_class": "carbohydrates"},
            {"food_name": "chicken", "confidence": 0.8, "food_class": "proteins"}
        ]

        result = engine.analyze_nutrition(detected_foods)

        assert "nutrition_profile" in result
        assert "balance_score" in result
        assert "missing_food_groups" in result
        assert "matching_rules" in result
        assert "detected_food_count" in result
        assert "food_classes_present" in result

        assert result["detected_food_count"] == 2
        assert isinstance(result["nutrition_profile"], dict)
        assert isinstance(result["balance_score"], float)
        assert isinstance(result["missing_food_groups"], list)

    def test_food_mapping_coverage(self):
        """Test that food mapping covers major Nigerian foods."""
        engine = NutritionAnalysisEngine()

        # Test some key Nigerian foods
        nigerian_foods = [
            "jollof_rice", "amala", "fufu", "pounded_yam",  # Carbs
            "beans", "moimoi", "chicken", "fish",  # Proteins
            "efo_riro", "okra", "ugwu",  # Minerals/vegetables
            "orange", "banana", "tomato",  # Vitamins/fruits
            "palm_oil", "groundnut",  # Fats
            "water", "zobo"  # Water
        ]

        for food in nigerian_foods:
            assert food in engine.food_class_mapping, f"Missing mapping for {food}"
            food_class = engine.food_class_mapping[food]
            assert food_class in [
                fc.value for fc in FoodClass], f"Invalid class for {food}"


class TestRuleOperators:
    """Test rule operator functionality."""

    def test_comparison_operators(self):
        """Test numeric comparison operators."""
        rule = NutritionRule(
            rule_id="test",
            name="Test",
            conditions=[],
            feedback_template="Test"
        )

        # Greater than
        assert rule._apply_operator(5, "gt", 3) is True
        assert rule._apply_operator(3, "gt", 5) is False

        # Less than
        assert rule._apply_operator(3, "lt", 5) is True
        assert rule._apply_operator(5, "lt", 3) is False

        # Equal
        assert rule._apply_operator(5, "eq", 5) is True
        assert rule._apply_operator(5, "eq", 3) is False

        # Greater equal
        assert rule._apply_operator(5, "gte", 5) is True
        assert rule._apply_operator(5, "gte", 3) is True
        assert rule._apply_operator(3, "gte", 5) is False

    def test_list_operators(self):
        """Test list-based operators."""
        rule = NutritionRule(
            rule_id="test",
            name="Test",
            conditions=[],
            feedback_template="Test"
        )

        # In operator
        assert rule._apply_operator("apple", "in", ["apple", "banana"]) is True
        assert rule._apply_operator(
            "orange", "in", ["apple", "banana"]) is False

        # Not in operator
        assert rule._apply_operator(
            "orange", "not_in", ["apple", "banana"]) is True
        assert rule._apply_operator(
            "apple", "not_in", ["apple", "banana"]) is False

        # Contains operator
        assert rule._apply_operator(
            ["apple", "banana"], "contains", "apple") is True
        assert rule._apply_operator(
            ["apple", "banana"], "contains", "orange") is False
        assert rule._apply_operator("hello world", "contains", "world") is True
        assert rule._apply_operator("hello world", "contains", "xyz") is False


if __name__ == "__main__":
    pytest.main([__file__])
