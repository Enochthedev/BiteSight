"""Meals, detected foods and the Nigerian food catalogue."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text, func

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from .base import UUID, Base, TimestampMixin, uuid_pk


class Meal(Base, TimestampMixin):
    __tablename__ = "meals"

    id = uuid_pk()
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    image_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    analysis_status = Column(String(50), default="pending", index=True)

    student = relationship("Student", back_populates="meals")
    detected_foods = relationship("DetectedFood", back_populates="meal", cascade="all, delete-orphan")
    feedback_records = relationship("FeedbackRecord", back_populates="meal", cascade="all, delete-orphan")


class DetectedFood(Base, TimestampMixin):
    __tablename__ = "detected_foods"

    id = uuid_pk()
    meal_id = Column(UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False, index=True)
    food_name = Column(String(255), nullable=False)
    confidence_score = Column(Numeric(3, 2))
    food_class = Column(String(100), nullable=False, index=True)
    bounding_box = Column(JSON)

    meal = relationship("Meal", back_populates="detected_foods")


class NigerianFood(Base, TimestampMixin):
    __tablename__ = "nigerian_foods"

    id = uuid_pk()
    food_name = Column(String(255), nullable=False, index=True)
    local_names = Column(JSON)
    food_class = Column(String(100), nullable=False, index=True)
    nutritional_info = Column(JSON)
    cultural_context = Column(Text)


class FoodDetectionResult(BaseModel):
    food_name: str
    confidence: float = Field(..., ge=0, le=1)
    food_class: str
    bounding_box: Optional[Dict[str, float]] = None


class MealUploadRequest(BaseModel):
    student_id: PyUUID
    timestamp: datetime = Field(default_factory=datetime.now)


class NigerianFoodCreate(BaseModel):
    food_name: str = Field(..., min_length=1, max_length=255)
    local_names: Optional[Dict[str, Any]] = None
    food_class: str = Field(..., min_length=1, max_length=100)
    nutritional_info: Optional[Dict[str, Any]] = None
    cultural_context: Optional[str] = None


class NigerianFoodUpdate(BaseModel):
    food_name: Optional[str] = Field(None, min_length=1, max_length=255)
    local_names: Optional[Dict[str, Any]] = None
    food_class: Optional[str] = Field(None, min_length=1, max_length=100)
    nutritional_info: Optional[Dict[str, Any]] = None
    cultural_context: Optional[str] = None


class NigerianFoodResponse(NigerianFoodCreate):
    model_config = ConfigDict(from_attributes=True)

    id: PyUUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NigerianFoodBulkCreate(BaseModel):
    foods: List[NigerianFoodCreate]


class NigerianFoodBulkResponse(BaseModel):
    created_count: int
    failed_count: int
    created_foods: List[NigerianFoodResponse] = []
    errors: List[str] = []


class NigerianFoodSearchRequest(BaseModel):
    query: Optional[str] = None
    food_class: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=500)


class NigerianFoodSearchResponse(BaseModel):
    foods: List[NigerianFoodResponse]
    total_count: int
    skip: int
    limit: int
