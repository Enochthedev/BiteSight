"""ORM models and API schemas. Importing this package registers every table on Base.metadata."""

from .base import Base
from .user import Student, User
from .meal import DetectedFood, Meal, NigerianFood
from .feedback import FeedbackRecord, NutritionRule
from .history import WeeklyInsight
from .consent import ConsentRecord
from .admin import (
    AdminPermission,
    AdminRole,
    AdminRolePermission,
    AdminSession,
    AdminUser,
)
from .image_metadata import ImageMetadata

__all__ = [
    "Base",
    "Student",
    "User",
    "Meal",
    "DetectedFood",
    "NigerianFood",
    "FeedbackRecord",
    "NutritionRule",
    "WeeklyInsight",
    "ConsentRecord",
    "AdminUser",
    "AdminRole",
    "AdminPermission",
    "AdminRolePermission",
    "AdminSession",
    "ImageMetadata",
]
