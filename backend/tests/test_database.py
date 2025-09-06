"""Tests for database operations and utilities."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.core.database_utils import (
    create_database_tables,
    drop_database_tables,
    check_database_connection,
    initialize_sample_data,
    reset_database
)
from app.models.meal import NigerianFood
from app.models.feedback import NutritionRule


class TestDatabaseUtils:
    """Test database utility functions."""

    def test_check_database_connection_success(self, db_session):
        """Test successful database connection check."""
        # The db_session fixture ensures we have a working connection
        assert check_database_connection() is True

    @patch('app.core.database_utils.engine')
    def test_check_database_connection_failure(self, mock_engine):
        """Test failed database connection check."""
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")

        assert check_database_connection() is False

    def test_initialize_sample_data_success(self, db_session):
        """Test successful sample data initialization."""
        # Should succeed on empty database
        assert initialize_sample_data(db_session) is True

        # Check that data was actually inserted
        foods = db_session.query(NigerianFood).all()
        rules = db_session.query(NutritionRule).all()

        assert len(foods) > 0
        assert len(rules) > 0

        # Verify specific sample data
        jollof = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Jollof Rice"
        ).first()
        assert jollof is not None
        assert jollof.food_class == "carbohydrates"

        protein_rule = db_session.query(NutritionRule).filter(
            NutritionRule.rule_name == "Missing Protein Check"
        ).first()
        assert protein_rule is not None
        assert protein_rule.is_active is True

    def test_initialize_sample_data_already_exists(self, db_session):
        """Test sample data initialization when data already exists."""
        # First initialization
        assert initialize_sample_data(db_session) is True

        # Second initialization should skip
        assert initialize_sample_data(db_session) is True

        # Should not duplicate data
        foods = db_session.query(NigerianFood).all()
        assert len(foods) == 5  # Should still be 5, not 10

    def test_initialize_sample_data_failure(self, db_session):
        """Test sample data initialization failure."""
        # Mock a database error during commit
        with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("Commit failed")):
            assert initialize_sample_data(db_session) is False

    def test_sample_data_content(self, db_session):
        """Test the content of initialized sample data."""
        assert initialize_sample_data(db_session) is True

        # Test Nigerian foods
        foods = db_session.query(NigerianFood).all()
        food_names = [food.food_name for food in foods]

        expected_foods = ["Jollof Rice", "Amala",
                          "Efo Riro", "Suya", "Moi Moi"]
        for expected_food in expected_foods:
            assert expected_food in food_names

        # Test food classes distribution
        food_classes = [food.food_class for food in foods]
        assert "carbohydrates" in food_classes
        assert "proteins" in food_classes
        assert "vitamins" in food_classes

        # Test nutrition rules
        rules = db_session.query(NutritionRule).all()
        rule_names = [rule.rule_name for rule in rules]

        expected_rules = [
            "Missing Protein Check",
            "Missing Vegetables Check",
            "Balanced Meal Praise",
            "Too Much Carbs Warning"
        ]
        for expected_rule in expected_rules:
            assert expected_rule in rule_names

        # Test rule priorities
        priorities = [rule.priority for rule in rules]
        assert 1 in priorities  # Should have priority 1 rules
        assert 2 in priorities  # Should have priority 2 rules

        # Test all rules are active
        active_rules = [rule for rule in rules if rule.is_active]
        assert len(active_rules) == len(rules)  # All should be active

    def test_nigerian_food_local_names(self, db_session):
        """Test that Nigerian foods have proper local names."""
        assert initialize_sample_data(db_session) is True

        # Test Jollof Rice local names
        jollof = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Jollof Rice"
        ).first()
        assert jollof.local_names is not None
        assert "yoruba" in jollof.local_names
        assert "igbo" in jollof.local_names
        assert "hausa" in jollof.local_names

        # Test Amala local names (Yoruba specific)
        amala = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Amala"
        ).first()
        assert amala.local_names is not None
        assert "yoruba" in amala.local_names

        # Test Suya local names (Hausa specific)
        suya = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Suya"
        ).first()
        assert suya.local_names is not None
        assert "hausa" in suya.local_names

    def test_nutrition_rule_condition_logic(self, db_session):
        """Test that nutrition rules have proper condition logic."""
        assert initialize_sample_data(db_session) is True

        # Test missing protein rule
        protein_rule = db_session.query(NutritionRule).filter(
            NutritionRule.rule_name == "Missing Protein Check"
        ).first()
        assert protein_rule.condition_logic is not None
        assert "missing_food_groups" in protein_rule.condition_logic
        assert "proteins" in protein_rule.condition_logic["missing_food_groups"]

        # Test balanced meal rule
        balanced_rule = db_session.query(NutritionRule).filter(
            NutritionRule.rule_name == "Balanced Meal Praise"
        ).first()
        assert balanced_rule.condition_logic is not None
        assert "all_food_groups_present" in balanced_rule.condition_logic
        assert balanced_rule.condition_logic["all_food_groups_present"] is True

        # Test carb ratio rule
        carb_rule = db_session.query(NutritionRule).filter(
            NutritionRule.rule_name == "Too Much Carbs Warning"
        ).first()
        assert carb_rule.condition_logic is not None
        assert "carbohydrate_ratio" in carb_rule.condition_logic
        assert carb_rule.condition_logic["carbohydrate_ratio"] == ">0.7"

    def test_cultural_context_content(self, db_session):
        """Test that foods have meaningful cultural context."""
        assert initialize_sample_data(db_session) is True

        foods = db_session.query(NigerianFood).all()

        for food in foods:
            assert food.cultural_context is not None
            # Should have meaningful description
            assert len(food.cultural_context) > 10

        # Test specific cultural contexts
        jollof = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Jollof Rice"
        ).first()
        assert "celebration" in jollof.cultural_context.lower()

        moi_moi = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Moi Moi"
        ).first()
        assert "protein" in moi_moi.cultural_context.lower()

    def test_nutritional_info_structure(self, db_session):
        """Test that foods have proper nutritional information."""
        assert initialize_sample_data(db_session) is True

        foods = db_session.query(NigerianFood).all()

        for food in foods:
            assert food.nutritional_info is not None
            assert "calories_per_100g" in food.nutritional_info
            assert isinstance(
                food.nutritional_info["calories_per_100g"], (int, float))
            assert food.nutritional_info["calories_per_100g"] > 0

        # Test specific nutritional values
        suya = db_session.query(NigerianFood).filter(
            NigerianFood.food_name == "Suya"
        ).first()
        # Suya should be high in protein
        assert suya.nutritional_info["protein"] > suya.nutritional_info["carbs"]
