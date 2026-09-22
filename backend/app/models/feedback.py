"""Feedback records and nutrition rules."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from .base import UUID, Base, TimestampMixin, uuid_pk


class FeedbackRecord(Base, TimestampMixin):
    __tablename__ = "feedback_records"

    id = uuid_pk()
    meal_id = Column(
        UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False, index=True
    )
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    feedback_text = Column(Text, nullable=False)
    feedback_type = Column(String(100))
    recommendations = Column(JSON)
    feedback_date = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    meal = relationship("Meal", back_populates="feedback_records")
    student = relationship("Student", back_populates="feedback_records")


class NutritionRule(Base, TimestampMixin):
    __tablename__ = "nutrition_rules"

    id = uuid_pk()
    rule_name = Column(String(255), nullable=False, index=True)
    condition_logic = Column(JSON)
    feedback_template = Column(Text, nullable=False)
    priority = Column(Integer, default=1, index=True)
    is_active = Column(Boolean, default=True, index=True)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PyUUID
    meal_id: PyUUID
    student_id: PyUUID
    feedback_text: str
    feedback_type: Optional[str] = None
    recommendations: Optional[Any] = None
    feedback_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NutritionFeedback(BaseModel):
    """Feedback generated for one analysed meal (not persisted directly)."""

    meal_id: PyUUID
    detected_foods: List[Dict[str, Any]] = []
    missing_food_groups: List[str] = []
    recommendations: List[str] = []
    overall_balance_score: float = Field(0.0, ge=0, le=1)
    feedback_message: str = ""


class NutritionRuleCreate(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=255)
    condition_logic: Dict[str, Any] = {}
    feedback_template: str = Field(..., min_length=1)
    priority: int = Field(1, ge=1)
    is_active: bool = True


class NutritionRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    condition_logic: Optional[Dict[str, Any]] = None
    feedback_template: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class NutritionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PyUUID
    rule_name: str
    condition_logic: Optional[Dict[str, Any]] = None
    feedback_template: str
    priority: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
