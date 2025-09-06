"""Data validation utilities and functions."""

import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.models.user import Student
from app.models.meal import Meal, NigerianFood


class ValidationError(Exception):
    """Custom validation error."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ImageValidation:
    """Image validation utilities."""

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_DIMENSIONS = (224, 224)  # Minimum width, height
    MAX_DIMENSIONS = (4096, 4096)  # Maximum width, height

    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """
        Validate image file extension.

        Args:
            filename: Name of the file

        Returns:
            bool: True if valid extension

        Raises:
            ValidationError: If extension is not allowed
        """
        if not filename:
            raise ValidationError("Filename cannot be empty", "filename")

        extension = filename.lower().split('.')[-1]
        if f'.{extension}' not in cls.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File extension '.{extension}' not allowed. "
                f"Allowed extensions: {', '.join(cls.ALLOWED_EXTENSIONS)}",
                "filename"
            )
        return True

    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """
        Validate image file size.

        Args:
            file_size: Size of file in bytes

        Returns:
            bool: True if valid size

        Raises:
            ValidationError: If file size exceeds limit
        """
        if file_size > cls.MAX_FILE_SIZE:
            raise ValidationError(
                f"File size {file_size} bytes exceeds maximum allowed size "
                f"{cls.MAX_FILE_SIZE} bytes ({cls.MAX_FILE_SIZE // (1024*1024)}MB)",
                "file_size"
            )
        return True

    @classmethod
    def validate_image_dimensions(cls, width: int, height: int) -> bool:
        """
        Validate image dimensions.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            bool: True if valid dimensions

        Raises:
            ValidationError: If dimensions are invalid
        """
        if width < cls.MIN_DIMENSIONS[0] or height < cls.MIN_DIMENSIONS[1]:
            raise ValidationError(
                f"Image dimensions {width}x{height} are too small. "
                f"Minimum dimensions: {cls.MIN_DIMENSIONS[0]}x{cls.MIN_DIMENSIONS[1]}",
                "dimensions"
            )

        if width > cls.MAX_DIMENSIONS[0] or height > cls.MAX_DIMENSIONS[1]:
            raise ValidationError(
                f"Image dimensions {width}x{height} are too large. "
                f"Maximum dimensions: {cls.MAX_DIMENSIONS[0]}x{cls.MAX_DIMENSIONS[1]}",
                "dimensions"
            )
        return True


class UserValidation:
    """User data validation utilities."""

    PASSWORD_MIN_LENGTH = 8
    PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)')

    @classmethod
    def validate_password_strength(cls, password: str) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            bool: True if password is strong enough

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            raise ValidationError(
                f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long",
                "password"
            )

        if not cls.PASSWORD_PATTERN.search(password):
            raise ValidationError(
                "Password must contain at least one lowercase letter, "
                "one uppercase letter, and one digit",
                "password"
            )
        return True

    @classmethod
    def validate_email_uniqueness(cls, email: str, db: Session, exclude_id: Optional[UUID] = None) -> bool:
        """
        Validate email uniqueness in database.

        Args:
            email: Email to validate
            db: Database session
            exclude_id: User ID to exclude from check (for updates)

        Returns:
            bool: True if email is unique

        Raises:
            ValidationError: If email already exists
        """
        query = db.query(Student).filter(Student.email == email)
        if exclude_id:
            query = query.filter(Student.id != exclude_id)

        existing_user = query.first()
        if existing_user:
            raise ValidationError(
                "Email address is already registered", "email")
        return True


class FoodValidation:
    """Food data validation utilities."""

    VALID_FOOD_CLASSES = {
        'carbohydrates', 'proteins', 'fats', 'vitamins', 'minerals', 'water'
    }

    @classmethod
    def validate_food_class(cls, food_class: str) -> bool:
        """
        Validate food class against allowed values.

        Args:
            food_class: Food class to validate

        Returns:
            bool: True if valid food class

        Raises:
            ValidationError: If food class is invalid
        """
        if food_class.lower() not in cls.VALID_FOOD_CLASSES:
            raise ValidationError(
                f"Invalid food class '{food_class}'. "
                f"Valid classes: {', '.join(cls.VALID_FOOD_CLASSES)}",
                "food_class"
            )
        return True

    @classmethod
    def validate_confidence_score(cls, confidence: float) -> bool:
        """
        Validate confidence score range.

        Args:
            confidence: Confidence score to validate

        Returns:
            bool: True if valid confidence score

        Raises:
            ValidationError: If confidence score is out of range
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValidationError(
                f"Confidence score {confidence} must be between 0.0 and 1.0",
                "confidence"
            )
        return True

    @classmethod
    def validate_bounding_box(cls, bounding_box: Optional[Dict[str, float]]) -> bool:
        """
        Validate bounding box coordinates.

        Args:
            bounding_box: Bounding box dictionary with x, y, width, height

        Returns:
            bool: True if valid bounding box

        Raises:
            ValidationError: If bounding box is invalid
        """
        if bounding_box is None:
            return True

        required_keys = {'x', 'y', 'width', 'height'}
        if not all(key in bounding_box for key in required_keys):
            raise ValidationError(
                f"Bounding box must contain keys: {', '.join(required_keys)}",
                "bounding_box"
            )

        for key, value in bounding_box.items():
            if not isinstance(value, (int, float)) or value < 0:
                raise ValidationError(
                    f"Bounding box {key} must be a non-negative number",
                    "bounding_box"
                )
        return True


class NutritionRuleValidation:
    """Nutrition rule validation utilities."""

    VALID_CONDITION_KEYS = {
        'missing_food_groups', 'all_food_groups_present', 'carbohydrate_ratio',
        'protein_ratio', 'fat_ratio', 'vitamin_ratio', 'mineral_ratio'
    }

    @classmethod
    def validate_condition_logic(cls, condition_logic: Dict[str, Any]) -> bool:
        """
        Validate nutrition rule condition logic.

        Args:
            condition_logic: Dictionary containing rule conditions

        Returns:
            bool: True if valid condition logic

        Raises:
            ValidationError: If condition logic is invalid
        """
        if not condition_logic:
            raise ValidationError(
                "Condition logic cannot be empty", "condition_logic")

        for key in condition_logic.keys():
            if key not in cls.VALID_CONDITION_KEYS:
                raise ValidationError(
                    f"Invalid condition key '{key}'. "
                    f"Valid keys: {', '.join(cls.VALID_CONDITION_KEYS)}",
                    "condition_logic"
                )

        # Validate specific condition types
        if 'missing_food_groups' in condition_logic:
            missing_groups = condition_logic['missing_food_groups']
            if not isinstance(missing_groups, list):
                raise ValidationError(
                    "missing_food_groups must be a list",
                    "condition_logic"
                )
            for group in missing_groups:
                FoodValidation.validate_food_class(group)

        # Validate ratio conditions
        ratio_keys = [k for k in condition_logic.keys()
                      if k.endswith('_ratio')]
        for ratio_key in ratio_keys:
            ratio_value = condition_logic[ratio_key]
            if isinstance(ratio_value, str) and ratio_value.startswith('>'):
                try:
                    float(ratio_value[1:])
                except ValueError:
                    raise ValidationError(
                        f"Invalid ratio condition format: {ratio_value}",
                        "condition_logic"
                    )
            elif not isinstance(ratio_value, (int, float)):
                raise ValidationError(
                    f"Ratio value must be a number or comparison string: {ratio_value}",
                    "condition_logic"
                )

        return True

    @classmethod
    def validate_feedback_template(cls, template: str) -> bool:
        """
        Validate feedback template content.

        Args:
            template: Feedback template string

        Returns:
            bool: True if valid template

        Raises:
            ValidationError: If template is invalid
        """
        if not template or not template.strip():
            raise ValidationError(
                "Feedback template cannot be empty", "feedback_template")

        if len(template) > 1000:
            raise ValidationError(
                "Feedback template cannot exceed 1000 characters",
                "feedback_template"
            )
        return True


def validate_uuid(uuid_string: str, field_name: str = "id") -> UUID:
    """
    Validate and convert UUID string.

    Args:
        uuid_string: String representation of UUID
        field_name: Name of the field for error reporting

    Returns:
        UUID: Validated UUID object

    Raises:
        ValidationError: If UUID is invalid
    """
    try:
        return UUID(uuid_string)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid UUID format for {field_name}", field_name)


def validate_date_range(start_date: Any, end_date: Any) -> bool:
    """
    Validate date range.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        bool: True if valid date range

    Raises:
        ValidationError: If date range is invalid
    """
    if start_date and end_date and start_date > end_date:
        raise ValidationError(
            "Start date cannot be after end date",
            "date_range"
        )
    return True
