"""Student accounts (table: students) and auth schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, Column, DateTime, Index, String, func
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, uuid_pk


class Student(Base, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (Index("ix_students_email", "email"),)

    id = uuid_pk()
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    history_enabled = Column(Boolean, default=False)

    meals = relationship("Meal", back_populates="student", cascade="all, delete-orphan")
    feedback_records = relationship("FeedbackRecord", back_populates="student", cascade="all, delete-orphan")
    weekly_insights = relationship("WeeklyInsight", back_populates="student", cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="student", cascade="all, delete-orphan")

    @property
    def student_id(self):
        """Alias for id; the workflow endpoints refer to current_user.student_id."""
        return self.id


# Generic alias used by a few endpoints
User = Student


class StudentCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    history_enabled: Optional[bool] = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PyUUID
    email: EmailStr
    name: str
    history_enabled: bool = False
    registration_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    student: StudentResponse
