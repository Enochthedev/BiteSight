"""Privacy consent records (table: consent_records) and schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID as PyUUID

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, func

from sqlalchemy.orm import relationship

from .base import UUID, Base, uuid_pk


class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        Index("ix_consent_records_student_type_date", "student_id", "consent_type", "consent_date"),
    )

    id = uuid_pk()
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(100), nullable=False, index=True)
    consent_given = Column(Boolean, nullable=False)
    consent_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    consent_version = Column(String(50))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student = relationship("Student", back_populates="consent_records")


class ConsentRequest(BaseModel):
    data_processing_consent: bool
    history_storage_consent: bool = False
    analytics_consent: bool = False
    consent_version: str = "1.0"


class ConsentUpdateRequest(BaseModel):
    history_storage_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None


class ConsentResponse(BaseModel):
    id: PyUUID
    student_id: PyUUID
    data_processing_consent: bool
    history_storage_consent: bool
    analytics_consent: bool
    consent_version: Optional[str] = None
    consent_date: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConsentHistoryResponse(BaseModel):
    consent_type: str
    consent_given: bool
    consent_date: datetime
    consent_version: Optional[str] = None
    ip_address: Optional[str] = None


class ConsentVerificationResult(BaseModel):
    has_data_processing_consent: bool
    has_history_storage_consent: bool
    has_analytics_consent: bool
    consent_date: Optional[datetime] = None
    requires_update: bool
    missing_consents: List[str] = []
