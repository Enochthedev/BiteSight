"""Consent management service."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status, Request

from app.models.consent import (
    ConsentRecord, ConsentRequest, ConsentResponse, ConsentUpdateRequest,
    ConsentHistoryResponse, ConsentVerificationResult
)
from app.models.user import Student


class ConsentService:
    """Service class for consent management operations."""

    def __init__(self, db: Session):
        self.db = db

    def record_consent(
        self,
        student_id: UUID,
        consent_data: ConsentRequest,
        request: Optional[Request] = None
    ) -> ConsentResponse:
        """Record user consent preferences."""
        # Get client IP and user agent for audit trail
        ip_address = None
        user_agent = None
        if request:
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get(
                "user-agent", "")[:500]  # Limit length

        # Record each consent type separately for granular tracking
        consent_records = []

        # Data processing consent (required)
        data_processing_record = ConsentRecord(
            student_id=student_id,
            consent_type="data_processing",
            consent_given=consent_data.data_processing_consent,
            consent_version=consent_data.consent_version,
            ip_address=ip_address,
            user_agent=user_agent
        )
        consent_records.append(data_processing_record)

        # History storage consent (required)
        history_storage_record = ConsentRecord(
            student_id=student_id,
            consent_type="history_storage",
            consent_given=consent_data.history_storage_consent,
            consent_version=consent_data.consent_version,
            ip_address=ip_address,
            user_agent=user_agent
        )
        consent_records.append(history_storage_record)

        # Analytics consent (optional)
        if consent_data.analytics_consent is not None:
            analytics_record = ConsentRecord(
                student_id=student_id,
                consent_type="analytics",
                consent_given=consent_data.analytics_consent,
                consent_version=consent_data.consent_version,
                ip_address=ip_address,
                user_agent=user_agent
            )
            consent_records.append(analytics_record)

        # Save all consent records
        for record in consent_records:
            self.db.add(record)

        # Update user's history_enabled flag based on history storage consent
        student = self.db.query(Student).filter(
            Student.id == student_id).first()
        if student:
            student.history_enabled = consent_data.history_storage_consent

        self.db.commit()

        # Return current consent status
        return self.get_current_consent(student_id)

    def update_consent(
        self,
        student_id: UUID,
        consent_updates: ConsentUpdateRequest,
        request: Optional[Request] = None
    ) -> ConsentResponse:
        """Update specific consent preferences."""
        # Get client IP and user agent for audit trail
        ip_address = None
        user_agent = None
        if request:
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")[:500]

        # Update each consent type that was provided
        if consent_updates.data_processing_consent is not None:
            record = ConsentRecord(
                student_id=student_id,
                consent_type="data_processing",
                consent_given=consent_updates.data_processing_consent,
                consent_version="1.0",  # Could be made configurable
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(record)

        if consent_updates.history_storage_consent is not None:
            record = ConsentRecord(
                student_id=student_id,
                consent_type="history_storage",
                consent_given=consent_updates.history_storage_consent,
                consent_version="1.0",
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(record)

            # Update user's history_enabled flag
            student = self.db.query(Student).filter(
                Student.id == student_id).first()
            if student:
                student.history_enabled = consent_updates.history_storage_consent

        if consent_updates.analytics_consent is not None:
            record = ConsentRecord(
                student_id=student_id,
                consent_type="analytics",
                consent_given=consent_updates.analytics_consent,
                consent_version="1.0",
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(record)

        self.db.commit()

        return self.get_current_consent(student_id)

    def get_current_consent(self, student_id: UUID) -> ConsentResponse:
        """Get current consent status for a user."""
        # Get the latest consent record for each type
        consent_types = ["data_processing", "history_storage", "analytics"]
        current_consents = {}
        consent_date = None

        for consent_type in consent_types:
            latest_record = (
                self.db.query(ConsentRecord)
                .filter(
                    ConsentRecord.student_id == student_id,
                    ConsentRecord.consent_type == consent_type
                )
                .order_by(desc(ConsentRecord.consent_date))
                .first()
            )

            if latest_record:
                current_consents[consent_type] = latest_record.consent_given
                if consent_date is None or latest_record.consent_date > consent_date:
                    consent_date = latest_record.consent_date
            else:
                current_consents[consent_type] = False

        return ConsentResponse(
            id=student_id,  # Using student_id as the response ID
            student_id=student_id,
            data_processing_consent=current_consents.get(
                "data_processing", False),
            history_storage_consent=current_consents.get(
                "history_storage", False),
            analytics_consent=current_consents.get("analytics", False),
            consent_date=consent_date or datetime.utcnow(),
            consent_version="1.0",
            created_at=consent_date or datetime.utcnow(),
            updated_at=consent_date or datetime.utcnow()
        )

    def verify_consent(self, student_id: UUID, required_consents: List[str]) -> ConsentVerificationResult:
        """Verify that user has given required consents."""
        current_consent = self.get_current_consent(student_id)

        has_data_processing = current_consent.data_processing_consent
        has_history_storage = current_consent.history_storage_consent
        has_analytics = current_consent.analytics_consent

        missing_consents = []

        if "data_processing" in required_consents and not has_data_processing:
            missing_consents.append("data_processing")

        if "history_storage" in required_consents and not has_history_storage:
            missing_consents.append("history_storage")

        if "analytics" in required_consents and not has_analytics:
            missing_consents.append("analytics")

        return ConsentVerificationResult(
            has_data_processing_consent=has_data_processing,
            has_history_storage_consent=has_history_storage,
            has_analytics_consent=has_analytics,
            consent_date=current_consent.consent_date,
            requires_update=len(missing_consents) > 0,
            missing_consents=missing_consents
        )

    def get_consent_history(self, student_id: UUID) -> List[ConsentHistoryResponse]:
        """Get consent history for a user."""
        records = (
            self.db.query(ConsentRecord)
            .filter(ConsentRecord.student_id == student_id)
            .order_by(desc(ConsentRecord.consent_date))
            .all()
        )

        return [
            ConsentHistoryResponse(
                consent_type=record.consent_type,
                consent_given=record.consent_given,
                consent_date=record.consent_date,
                consent_version=record.consent_version or "1.0",
                ip_address=record.ip_address
            )
            for record in records
        ]

    def revoke_all_consents(self, student_id: UUID, request: Optional[Request] = None) -> bool:
        """Revoke all consents for a user (for data deletion requests)."""
        # Get client IP and user agent for audit trail
        ip_address = None
        user_agent = None
        if request:
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")[:500]

        # Record revocation for all consent types
        consent_types = ["data_processing", "history_storage", "analytics"]

        for consent_type in consent_types:
            revocation_record = ConsentRecord(
                student_id=student_id,
                consent_type=consent_type,
                consent_given=False,
                consent_version="1.0",
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(revocation_record)

        # Update user's history_enabled flag
        student = self.db.query(Student).filter(
            Student.id == student_id).first()
        if student:
            student.history_enabled = False

        self.db.commit()
        return True

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return None
