"""Weekly insights (table: weekly_insights) and history schemas."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Text, func

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from .base import UUID, Base, TimestampMixin, uuid_pk


class WeeklyInsight(Base, TimestampMixin):
    __tablename__ = "weekly_insights"
    __table_args__ = (
        Index("ix_weekly_insights_student_week", "student_id", "week_start_date", unique=True),
    )

    id = uuid_pk()
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False, index=True)
    week_end_date = Column(Date, nullable=False)
    nutrition_summary = Column(JSON)
    recommendations = Column(Text)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student", back_populates="weekly_insights")


class MealHistoryRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class MealHistoryResponse(BaseModel):
    meals: List[Dict[str, Any]]
    total_count: int
    has_more: bool
    limit: int
    offset: int


class NutritionSummary(BaseModel):
    """Share of meals (0-1) containing each food group, plus overall balance."""

    carbohydrates_frequency: float = Field(0.0, ge=0, le=1)
    proteins_frequency: float = Field(0.0, ge=0, le=1)
    fats_frequency: float = Field(0.0, ge=0, le=1)
    vitamins_frequency: float = Field(0.0, ge=0, le=1)
    minerals_frequency: float = Field(0.0, ge=0, le=1)
    water_frequency: float = Field(0.0, ge=0, le=1)
    balance_score: float = Field(0.0, ge=0, le=1)


class InsightGenerationRequest(BaseModel):
    week_start_date: Optional[date] = None
    force_regenerate: bool = False


class WeeklyInsightResponse(BaseModel):
    student_id: PyUUID
    week_period: str
    meals_analyzed: int
    nutrition_balance: Dict[str, float]
    improvement_areas: List[str]
    positive_trends: List[str]
    recommendations: str
    generated_at: datetime
