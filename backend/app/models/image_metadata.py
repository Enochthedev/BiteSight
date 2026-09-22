"""Uploaded meal image metadata (table: image_metadata).

Note: unlike the other tables, image_metadata has no Alembic migration in this
repo; it is created via Base.metadata.create_all.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func


from sqlalchemy.dialects.postgresql import JSON

from .base import UUID, Base, TimestampMixin, uuid_pk


class ImageMetadata(Base, TimestampMixin):
    __tablename__ = "image_metadata"

    id = uuid_pk()
    meal_id = Column(UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False, unique=True, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    original_filename = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    format = Column(String(20))
    mode = Column(String(20))
    width = Column(Integer)
    height = Column(Integer)
    file_hash = Column(String(64), index=True)
    raw_image_path = Column(String(500))
    processed_image_path = Column(String(500))
    thumbnail_path = Column(String(500))
    quality_score = Column(Float)
    quality_issues = Column(JSON)
    quality_warnings = Column(JSON)
    exif_data = Column(JSON)
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_date = Column(DateTime(timezone=True))


class ImageMetadataCreate(BaseModel):
    meal_id: PyUUID
    student_id: PyUUID
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    format: Optional[str] = None
    mode: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_hash: Optional[str] = None
    raw_image_path: Optional[str] = None
    processed_image_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    quality_score: Optional[float] = None
    quality_issues: List[str] = []
    quality_warnings: List[str] = []
    exif_data: Optional[Dict[str, Any]] = None
    is_processed: bool = False
    processing_error: Optional[str] = None


class ImageMetadataUpdate(BaseModel):
    processed_image_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    quality_score: Optional[float] = None
    quality_issues: Optional[List[str]] = None
    quality_warnings: Optional[List[str]] = None
    is_processed: Optional[bool] = None
    processing_error: Optional[str] = None


class ImageMetadataResponse(ImageMetadataCreate):
    model_config = ConfigDict(from_attributes=True)

    id: PyUUID
    upload_date: Optional[datetime] = None
    processed_date: Optional[datetime] = None


class ImageSearchQuery(BaseModel):
    student_id: Optional[PyUUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_quality_score: Optional[float] = Field(None, ge=0, le=1)
    has_processing_errors: Optional[bool] = None
    image_format: Optional[str] = None
    min_resolution: Optional[int] = Field(None, ge=0, description="Minimum width*height in pixels")
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class ImageSearchResponse(BaseModel):
    images: List[ImageMetadataResponse]
    total_count: int
    has_more: bool
