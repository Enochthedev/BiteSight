"""Tests for consent management functionality."""

import pytest
from datetime import datetime
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.consent import (
    ConsentRecord, ConsentRequest, ConsentUpdateRequest, ConsentVerificationResult
)
from app.models.user import Student, StudentCreate
from app.services.consent_service import ConsentService
from app.services.user_service import UserService
from app.core.consent_middleware import ConsentRequiredError, require_consent


class TestConsentService:
    """Test consent service operations."""

    def test_record_consent_success(self, db_session: Session):
        """Test successful consent recording."""
        # Create a user first
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="consent@example.com",
            name="Consent User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        # Record consent
        consent_service = ConsentService(db_session)
        consent_data = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=True,
            analytics_consent=False,
            consent_version="1.0"
        )

        result = consent_service.record_consent(user.id, consent_data)

        assert result.student_id == user.id
        assert result.data_processing_consent is True
        assert result.history_storage_consent is True
        assert result.analytics_consent is False
        assert result.consent_version == "1.0"

        # Verify records were created in database
        records = db_session.query(ConsentRecord).filter(
            ConsentRecord.student_id == user.id
        ).all()

        assert len(records) == 3  # data_processing, history_storage, analytics

        # Verify user's history_enabled flag was updated
        updated_user = db_session.query(Student).filter(
            Student.id == user.id).first()
        assert updated_user.history_enabled is True

    def test_update_consent(self, db_session: Session):
        """Test consent updates."""
        # Create user and initial consent
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="update@example.com",
            name="Update User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        consent_service = ConsentService(db_session)

        # Initial consent
        initial_consent = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=False,
            analytics_consent=False
        )
        consent_service.record_consent(user.id, initial_consent)

        # Update consent
        update_data = ConsentUpdateRequest(
            history_storage_consent=True,
            analytics_consent=True
        )

        result = consent_service.update_consent(user.id, update_data)

        assert result.data_processing_consent is True  # Unchanged
        assert result.history_storage_consent is True  # Updated
        assert result.analytics_consent is True  # Updated

        # Verify user's history_enabled flag was updated
        updated_user = db_session.query(Student).filter(
            Student.id == user.id).first()
        assert updated_user.history_enabled is True

    def test_get_current_consent(self, db_session: Session):
        """Test getting current consent status."""
        # Create user
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="current@example.com",
            name="Current User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        consent_service = ConsentService(db_session)

        # Record consent
        consent_data = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=True,
            analytics_consent=False
        )
        consent_service.record_consent(user.id, consent_data)

        # Get current consent
        current = consent_service.get_current_consent(user.id)

        assert current.student_id == user.id
        assert current.data_processing_consent is True
        assert current.history_storage_consent is True
        assert current.analytics_consent is False

    def test_verify_consent_success(self, db_session: Session):
        """Test consent verification when all required consents are given."""
        # Create user and consent
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="verify@example.com",
            name="Verify User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        consent_service = ConsentService(db_session)
        consent_data = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=True,
            analytics_consent=True
        )
        consent_service.record_consent(user.id, consent_data)

        # Verify consent
        result = consent_service.verify_consent(
            user.id,
            ["data_processing", "history_storage"]
        )

        assert result.has_data_processing_consent is True
        assert result.has_history_storage_consent is True
        assert result.requires_update is False
        assert len(result.missing_consents) == 0

    def test_verify_consent_missing(self, db_session: Session):
        """Test consent verification when required consents are missing."""
        # Create user with partial consent
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="missing@example.com",
            name="Missing User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        consent_service = ConsentService(db_session)
        consent_data = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=False,
            analytics_consent=False
        )
        consent_service.record_consent(user.id, consent_data)

        # Verify consent
        result = consent_service.verify_consent(
            user.id,
            ["data_processing", "history_storage", "analytics"]
        )

        assert result.has_data_processing_consent is True
        assert result.has_history_storage_consent is False
        assert result.has_analytics_consent is False
        assert result.requires_update is True
        assert "history_storage" in result.missing_consents
        assert "analytics" in result.missing_consents

    def test_get_consent_history(self, db_session: Session):
        """Test getting consent history."""
        # Create user
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="history@example.com",
            name="History User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        consent_service = ConsentService(db_session)

        # Record initial consent
        initial_consent = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=False,
            analytics_consent=False
        )
        consent_service.record_consent(user.id, initial_consent)

        # Update consent
        update_data = ConsentUpdateRequest(history_storage_consent=True)
        consent_service.update_consent(user.id, update_data)

        # Get history
        history = consent_service.get_consent_history(user.id)

        # Should have records for the update and initial consent
        assert len(history) >= 4  # At least 3 initial + 1 update

        # Check that history is ordered by date (newest first)
        for i in range(len(history) - 1):
            assert history[i].consent_date >= history[i + 1].consent_date

    def test_revoke_all_consents(self, db_session: Session):
        """Test revoking all consents."""
        # Create user with consents
        user_service = UserService(db_session)
        user_data = StudentCreate(
            email="revoke@example.com",
            name="Revoke User",
            password="password123"
        )
        user = user_service.create_user(user_data)

        consent_service = ConsentService(db_session)

        # Record consent
        consent_data = ConsentRequest(
            data_processing_consent=True,
            history_storage_consent=True,
            analytics_consent=True
        )
        consent_service.record_consent(user.id, consent_data)

        # Revoke all consents
        success = consent_service.revoke_all_consents(user.id)
        assert success is True

        # Verify all consents are now False
        current = consent_service.get_current_consent(user.id)
        assert current.data_processing_consent is False
        assert current.history_storage_consent is False
        assert current.analytics_consent is False

        # Verify user's history_enabled flag was updated
        updated_user = db_session.query(Student).filter(
            Student.id == user.id).first()
        assert updated_user.history_enabled is False


class TestConsentMiddleware:
    """Test consent middleware functionality."""

    def test_consent_required_error(self):
        """Test ConsentRequiredError creation."""
        missing_consents = ["data_processing", "history_storage"]
        error = ConsentRequiredError(missing_consents)

        assert error.status_code == 403
        assert error.detail["error"] == "consent_required"
        assert error.detail["missing_consents"] == missing_consents

    def test_require_consent_dependency_factory(self):
        """Test that require_consent creates proper dependency function."""
        required_consents = ["data_processing"]
        dependency = require_consent(required_consents)

        assert callable(dependency)
        # The actual dependency testing would require a full FastAPI test setup


class TestConsentEndpoints:
    """Test consent management API endpoints."""

    def test_record_consent_endpoint(self, client: TestClient, db_session: Session):
        """Test consent recording endpoint."""
        # Register and login user
        user_data = {
            "email": "consentapi@example.com",
            "name": "Consent API User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "consentapi@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Record consent
        consent_data = {
            "data_processing_consent": True,
            "history_storage_consent": True,
            "analytics_consent": False,
            "consent_version": "1.0"
        }

        response = client.post(
            "/api/v1/consent/", json=consent_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["data_processing_consent"] is True
        assert data["history_storage_consent"] is True
        assert data["analytics_consent"] is False

    def test_get_current_consent_endpoint(self, client: TestClient, db_session: Session):
        """Test getting current consent endpoint."""
        # Register and login user
        user_data = {
            "email": "getconsent@example.com",
            "name": "Get Consent User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "getconsent@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Record consent first
        consent_data = {
            "data_processing_consent": True,
            "history_storage_consent": False,
            "analytics_consent": True
        }
        client.post("/api/v1/consent/", json=consent_data, headers=headers)

        # Get current consent
        response = client.get("/api/v1/consent/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data_processing_consent"] is True
        assert data["history_storage_consent"] is False
        assert data["analytics_consent"] is True

    def test_update_consent_endpoint(self, client: TestClient, db_session: Session):
        """Test consent update endpoint."""
        # Register and login user
        user_data = {
            "email": "updateconsent@example.com",
            "name": "Update Consent User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "updateconsent@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Record initial consent
        initial_consent = {
            "data_processing_consent": True,
            "history_storage_consent": False,
            "analytics_consent": False
        }
        client.post("/api/v1/consent/", json=initial_consent, headers=headers)

        # Update consent
        update_data = {
            "history_storage_consent": True,
            "analytics_consent": True
        }

        response = client.put("/api/v1/consent/",
                              json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data_processing_consent"] is True  # Unchanged
        assert data["history_storage_consent"] is True  # Updated
        assert data["analytics_consent"] is True  # Updated

    def test_verify_consent_endpoint(self, client: TestClient, db_session: Session):
        """Test consent verification endpoint."""
        # Register and login user
        user_data = {
            "email": "verifyconsent@example.com",
            "name": "Verify Consent User",
            "password": "password123"
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post("/api/v1/auth/login", json={
            "email": "verifyconsent@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Record partial consent
        consent_data = {
            "data_processing_consent": True,
            "history_storage_consent": False,
            "analytics_consent": False
        }
        client.post("/api/v1/consent/", json=consent_data, headers=headers)

        # Verify consent
        required_consents = ["data_processing", "history_storage"]

        response = client.post(
            "/api/v1/consent/verify",
            json=required_consents,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data_processing_consent"] is True
        assert data["has_history_storage_consent"] is False
        assert data["requires_update"] is True
        assert "history_storage" in data["missing_consents"]

    def test_unauthorized_consent_access(self, client: TestClient):
        """Test accessing consent endpoints without authentication."""
        consent_data = {
            "data_processing_consent": True,
            "history_storage_consent": True
        }

        response = client.post("/api/v1/consent/", json=consent_data)
        assert response.status_code == 401

        response = client.get("/api/v1/consent/")
        assert response.status_code == 401

        response = client.put("/api/v1/consent/", json=consent_data)
        assert response.status_code == 401
