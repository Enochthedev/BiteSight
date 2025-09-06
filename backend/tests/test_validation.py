"""Tests for validation utilities."""

import pytest
from uuid import uuid4, UUID
from datetime import date

from app.core.validation import (
    ValidationError,
    ImageValidation,
    UserValidation,
    FoodValidation,
    NutritionRuleValidation,
    validate_uuid,
    validate_date_range
)
from app.models.user import Student


class TestImageValidation:
    """Test image validation utilities."""

    def test_validate_file_extension_valid(self):
        """Test valid file extensions."""
        assert ImageValidation.validate_file_extension("image.jpg") is True
        assert ImageValidation.validate_file_extension("image.jpeg") is True
        assert ImageValidation.validate_file_extension("image.png") is True
        assert ImageValidation.validate_file_extension(
            "IMAGE.JPG") is True  # Case insensitive

    def test_validate_file_extension_invalid(self):
        """Test invalid file extensions."""
        with pytest.raises(ValidationError) as exc_info:
            ImageValidation.validate_file_extension("image.gif")
        assert "not allowed" in str(exc_info.value)

        with pytest.raises(ValidationError):
            ImageValidation.validate_file_extension("image.bmp")

        with pytest.raises(ValidationError):
            ImageValidation.validate_file_extension("")

    def test_validate_file_size_valid(self):
        """Test valid file sizes."""
        assert ImageValidation.validate_file_size(1024) is True  # 1KB
        assert ImageValidation.validate_file_size(
            5 * 1024 * 1024) is True  # 5MB
        assert ImageValidation.validate_file_size(
            10 * 1024 * 1024) is True  # 10MB (max)

    def test_validate_file_size_invalid(self):
        """Test invalid file sizes."""
        with pytest.raises(ValidationError) as exc_info:
            ImageValidation.validate_file_size(15 * 1024 * 1024)  # 15MB
        assert "exceeds maximum" in str(exc_info.value)

    def test_validate_image_dimensions_valid(self):
        """Test valid image dimensions."""
        assert ImageValidation.validate_image_dimensions(
            224, 224) is True  # Minimum
        assert ImageValidation.validate_image_dimensions(
            1920, 1080) is True  # Common size
        assert ImageValidation.validate_image_dimensions(
            4096, 4096) is True  # Maximum

    def test_validate_image_dimensions_invalid(self):
        """Test invalid image dimensions."""
        # Too small
        with pytest.raises(ValidationError) as exc_info:
            ImageValidation.validate_image_dimensions(100, 100)
        assert "too small" in str(exc_info.value)

        # Too large
        with pytest.raises(ValidationError) as exc_info:
            ImageValidation.validate_image_dimensions(5000, 5000)
        assert "too large" in str(exc_info.value)


class TestUserValidation:
    """Test user validation utilities."""

    def test_validate_password_strength_valid(self):
        """Test valid passwords."""
        assert UserValidation.validate_password_strength("Password123") is True
        assert UserValidation.validate_password_strength(
            "MySecure1Pass") is True
        assert UserValidation.validate_password_strength("Test123ABC") is True

    def test_validate_password_strength_invalid(self):
        """Test invalid passwords."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            UserValidation.validate_password_strength("Pass1")
        assert "at least 8 characters" in str(exc_info.value)

        # No uppercase
        with pytest.raises(ValidationError) as exc_info:
            UserValidation.validate_password_strength("password123")
        assert "uppercase letter" in str(exc_info.value)

        # No lowercase
        with pytest.raises(ValidationError) as exc_info:
            UserValidation.validate_password_strength("PASSWORD123")
        assert "lowercase letter" in str(exc_info.value)

        # No digit
        with pytest.raises(ValidationError) as exc_info:
            UserValidation.validate_password_strength("Password")
        assert "digit" in str(exc_info.value)

    def test_validate_email_uniqueness(self, db_session):
        """Test email uniqueness validation."""
        # Create a student
        student = Student(
            email="existing@example.com",
            name="Existing User",
            password_hash="hashed_password"
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        # Test unique email
        assert UserValidation.validate_email_uniqueness(
            "new@example.com", db_session) is True

        # Test duplicate email
        with pytest.raises(ValidationError) as exc_info:
            UserValidation.validate_email_uniqueness(
                "existing@example.com", db_session)
        assert "already registered" in str(exc_info.value)

        # Test duplicate email with exclusion (for updates)
        assert UserValidation.validate_email_uniqueness(
            "existing@example.com",
            db_session,
            exclude_id=student.id
        ) is True


class TestFoodValidation:
    """Test food validation utilities."""

    def test_validate_food_class_valid(self):
        """Test valid food classes."""
        valid_classes = ['carbohydrates', 'proteins',
                         'fats', 'vitamins', 'minerals', 'water']
        for food_class in valid_classes:
            assert FoodValidation.validate_food_class(food_class) is True
            assert FoodValidation.validate_food_class(
                food_class.upper()) is True  # Case insensitive

    def test_validate_food_class_invalid(self):
        """Test invalid food classes."""
        with pytest.raises(ValidationError) as exc_info:
            FoodValidation.validate_food_class("invalid_class")
        assert "Invalid food class" in str(exc_info.value)

    def test_validate_confidence_score_valid(self):
        """Test valid confidence scores."""
        assert FoodValidation.validate_confidence_score(0.0) is True
        assert FoodValidation.validate_confidence_score(0.5) is True
        assert FoodValidation.validate_confidence_score(1.0) is True

    def test_validate_confidence_score_invalid(self):
        """Test invalid confidence scores."""
        with pytest.raises(ValidationError) as exc_info:
            FoodValidation.validate_confidence_score(-0.1)
        assert "between 0.0 and 1.0" in str(exc_info.value)

        with pytest.raises(ValidationError):
            FoodValidation.validate_confidence_score(1.1)

    def test_validate_bounding_box_valid(self):
        """Test valid bounding boxes."""
        # None is valid
        assert FoodValidation.validate_bounding_box(None) is True

        # Valid bounding box
        valid_box = {"x": 10.0, "y": 20.0, "width": 100.0, "height": 80.0}
        assert FoodValidation.validate_bounding_box(valid_box) is True

        # Integer values are also valid
        valid_box_int = {"x": 10, "y": 20, "width": 100, "height": 80}
        assert FoodValidation.validate_bounding_box(valid_box_int) is True

    def test_validate_bounding_box_invalid(self):
        """Test invalid bounding boxes."""
        # Missing keys
        with pytest.raises(ValidationError) as exc_info:
            FoodValidation.validate_bounding_box({"x": 10, "y": 20})
        assert "must contain keys" in str(exc_info.value)

        # Negative values
        with pytest.raises(ValidationError) as exc_info:
            FoodValidation.validate_bounding_box(
                {"x": -10, "y": 20, "width": 100, "height": 80})
        assert "non-negative number" in str(exc_info.value)

        # Invalid value type
        with pytest.raises(ValidationError):
            FoodValidation.validate_bounding_box(
                {"x": "invalid", "y": 20, "width": 100, "height": 80})


class TestNutritionRuleValidation:
    """Test nutrition rule validation utilities."""

    def test_validate_condition_logic_valid(self):
        """Test valid condition logic."""
        # Missing food groups
        valid_logic1 = {"missing_food_groups": ["proteins", "vitamins"]}
        assert NutritionRuleValidation.validate_condition_logic(
            valid_logic1) is True

        # All food groups present
        valid_logic2 = {"all_food_groups_present": True}
        assert NutritionRuleValidation.validate_condition_logic(
            valid_logic2) is True

        # Ratio conditions
        valid_logic3 = {"carbohydrate_ratio": ">0.7"}
        assert NutritionRuleValidation.validate_condition_logic(
            valid_logic3) is True

        valid_logic4 = {"protein_ratio": 0.3}
        assert NutritionRuleValidation.validate_condition_logic(
            valid_logic4) is True

    def test_validate_condition_logic_invalid(self):
        """Test invalid condition logic."""
        # Empty logic
        with pytest.raises(ValidationError) as exc_info:
            NutritionRuleValidation.validate_condition_logic({})
        assert "cannot be empty" in str(exc_info.value)

        # Invalid key
        with pytest.raises(ValidationError) as exc_info:
            NutritionRuleValidation.validate_condition_logic(
                {"invalid_key": "value"})
        assert "Invalid condition key" in str(exc_info.value)

        # Invalid missing food groups (not a list)
        with pytest.raises(ValidationError) as exc_info:
            NutritionRuleValidation.validate_condition_logic(
                {"missing_food_groups": "proteins"})
        assert "must be a list" in str(exc_info.value)

        # Invalid food class in missing groups
        with pytest.raises(ValidationError):
            NutritionRuleValidation.validate_condition_logic(
                {"missing_food_groups": ["invalid_class"]})

        # Invalid ratio format
        with pytest.raises(ValidationError) as exc_info:
            NutritionRuleValidation.validate_condition_logic(
                {"carbohydrate_ratio": ">invalid"})
        assert "Invalid ratio condition format" in str(exc_info.value)

    def test_validate_feedback_template_valid(self):
        """Test valid feedback templates."""
        valid_template = "This is a valid feedback message."
        assert NutritionRuleValidation.validate_feedback_template(
            valid_template) is True

        # Long but valid template
        long_template = "A" * 999
        assert NutritionRuleValidation.validate_feedback_template(
            long_template) is True

    def test_validate_feedback_template_invalid(self):
        """Test invalid feedback templates."""
        # Empty template
        with pytest.raises(ValidationError) as exc_info:
            NutritionRuleValidation.validate_feedback_template("")
        assert "cannot be empty" in str(exc_info.value)

        # Whitespace only
        with pytest.raises(ValidationError):
            NutritionRuleValidation.validate_feedback_template("   ")

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            NutritionRuleValidation.validate_feedback_template("A" * 1001)
        assert "cannot exceed 1000 characters" in str(exc_info.value)


class TestUtilityValidation:
    """Test utility validation functions."""

    def test_validate_uuid_valid(self):
        """Test valid UUID validation."""
        test_uuid = uuid4()
        uuid_string = str(test_uuid)

        result = validate_uuid(uuid_string)
        assert isinstance(result, UUID)
        assert result == test_uuid

    def test_validate_uuid_invalid(self):
        """Test invalid UUID validation."""
        with pytest.raises(ValidationError) as exc_info:
            validate_uuid("invalid-uuid")
        assert "Invalid UUID format" in str(exc_info.value)

        with pytest.raises(ValidationError):
            validate_uuid("")

        with pytest.raises(ValidationError):
            validate_uuid("123")

    def test_validate_date_range_valid(self):
        """Test valid date ranges."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        assert validate_date_range(start_date, end_date) is True
        assert validate_date_range(None, end_date) is True
        assert validate_date_range(start_date, None) is True
        assert validate_date_range(None, None) is True

        # Same date
        assert validate_date_range(start_date, start_date) is True

    def test_validate_date_range_invalid(self):
        """Test invalid date ranges."""
        start_date = date(2024, 1, 31)
        end_date = date(2024, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(start_date, end_date)
        assert "cannot be after end date" in str(exc_info.value)
