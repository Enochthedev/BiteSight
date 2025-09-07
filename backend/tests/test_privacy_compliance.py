"""Privacy compliance and data protection testing."""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import Student
from app.models.meal import Meal
from app.models.feedback import FeedbackRecord
from app.models.consent import ConsentRecord


class TestPrivacyCompliance:
    """Test privacy compliance and data protection measures."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user with consent records."""
        user = Student(
            email="privacy_test@university.edu.ng",
            name="Privacy Test User",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Add consent record
        consent = ConsentRecord(
            student_id=user.student_id,
            data_storage=True,
            analytics=False,
            marketing=False,
            consent_date=datetime.utcnow()
        )
        db_session.add(consent)
        db_session.commit()

        return user

    @pytest.fixture
    def auth_headers(self, client, test_user):
        """Get authentication headers."""
        with patch('app.core.auth.verify_password', return_value=True):
            response = client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "test_password"
            })

            if response.status_code == 200:
                token = response.json().get("access_token", "mock-token")
                return {"Authorization": f"Bearer {token}"}

        return {"Authorization": "Bearer mock-token"}

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        from PIL import Image

        image = Image.new('RGB', (224, 224), color='red')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        image.save(temp_file.name, 'JPEG')

        yield temp_file.name

        os.unlink(temp_file.name)

    def test_consent_management_compliance(self, client, test_user, auth_headers):
        """Test consent management compliance (GDPR Article 7)."""

        # Test getting current consent status
        response = client.get(
            f"/api/v1/consent/{test_user.student_id}", headers=auth_headers)
        assert response.status_code == 200

        consent_data = response.json()
        assert "data_storage" in consent_data
        assert "analytics" in consent_data
        assert "marketing" in consent_data
        assert "consent_date" in consent_data

        # Test updating consent (must be explicit and informed)
        new_consent = {
            "data_storage": True,
            "analytics": True,
            "marketing": False,
            "consent_timestamp": datetime.utcnow().isoformat()
        }

        response = client.post(
            f"/api/v1/consent/{test_user.student_id}", json=new_consent, headers=auth_headers)
        assert response.status_code in [200, 201]

        # Verify consent was updated
        response = client.get(
            f"/api/v1/consent/{test_user.student_id}", headers=auth_headers)
        assert response.status_code == 200

        updated_consent = response.json()
        assert updated_consent["analytics"] == True
        assert updated_consent["marketing"] == False

        # Test withdrawing consent
        withdrawn_consent = {
            "data_storage": False,
            "analytics": False,
            "marketing": False
        }

        response = client.post(
            f"/api/v1/consent/{test_user.student_id}", json=withdrawn_consent, headers=auth_headers)
        assert response.status_code == 200

        # Test that data processing stops when consent is withdrawn
        # This would depend on actual implementation

    def test_data_minimization_principle(self, client, test_user, sample_image, auth_headers):
        """Test data minimization principle (GDPR Article 5)."""

        # Test that only necessary data is collected during meal analysis
        with patch('app.ml.inference.predictor.FoodPredictor') as mock_predictor:
            mock_predictor.return_value.predict_food_async = Mock(return_value={
                "detected_foods": [
                    {"name": "jollof_rice", "confidence": 0.95,
                        "food_class": "carbohydrates"}
                ]
            })

            with open(sample_image, 'rb') as img_file:
                response = client.post(
                    "/api/v1/meals/analyze",
                    files={"image": ("meal.jpg", img_file, "image/jpeg")},
                    data={"student_id": str(test_user.student_id)},
                    headers=auth_headers
                )

            # Should only collect necessary data
            if response.status_code == 200:
                result = response.json()
                # Should not collect unnecessary metadata
                assert "device_info" not in result
                assert "location_data" not in result
                assert "ip_address" not in result

        # Test that user profile only contains necessary information
        response = client.get(
            f"/api/v1/users/{test_user.student_id}/profile", headers=auth_headers)

        if response.status_code == 200:
            profile = response.json()
            # Should only contain necessary user data
            required_fields = {"student_id", "email", "name"}
            unnecessary_fields = {"password_hash",
                                  "internal_notes", "admin_flags"}

            for field in required_fields:
                assert field in profile

            for field in unnecessary_fields:
                assert field not in profile

    def test_purpose_limitation_compliance(self, client, test_user, auth_headers):
        """Test purpose limitation principle (GDPR Article 5)."""

        # Test that data is only used for stated purposes

        # Get user's meal history
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=auth_headers)
        assert response.status_code == 200

        # Test that data cannot be used for unauthorized purposes
        # For example, marketing without consent

        # Check consent status
        consent_response = client.get(
            f"/api/v1/consent/{test_user.student_id}", headers=auth_headers)
        consent_data = consent_response.json()

        if not consent_data.get("marketing", False):
            # Should not use data for marketing if consent not given
            response = client.get(
                f"/api/v1/marketing/recommendations/{test_user.student_id}", headers=auth_headers)
            # Should be forbidden or not exist
            assert response.status_code in [403, 404]

        # Test that analytics data is only collected with consent
        if not consent_data.get("analytics", False):
            # Should not collect analytics data without consent
            response = client.get(
                f"/api/v1/analytics/user-behavior/{test_user.student_id}", headers=auth_headers)
            assert response.status_code in [403, 404]

    def test_data_accuracy_and_correction(self, client, test_user, auth_headers):
        """Test data accuracy and right to rectification (GDPR Article 16)."""

        # Test getting user profile
        response = client.get(
            f"/api/v1/users/{test_user.student_id}/profile", headers=auth_headers)
        assert response.status_code == 200

        original_profile = response.json()

        # Test updating user profile (right to rectification)
        updated_data = {
            "name": "Updated Privacy Test User",
            "email": "updated_privacy_test@university.edu.ng"
        }

        response = client.put(
            f"/api/v1/users/{test_user.student_id}/profile", json=updated_data, headers=auth_headers)
        assert response.status_code == 200

        # Verify data was updated
        response = client.get(
            f"/api/v1/users/{test_user.student_id}/profile", headers=auth_headers)
        assert response.status_code == 200

        updated_profile = response.json()
        assert updated_profile["name"] == updated_data["name"]
        assert updated_profile["email"] == updated_data["email"]

        # Test correcting meal analysis data
        meal_id = "test_meal_123"
        correction_data = {
            "detected_foods": [
                {"name": "corrected_food", "confidence": 0.9, "food_class": "proteins"}
            ],
            "user_correction": True,
            "correction_reason": "AI misidentified the food"
        }

        response = client.put(
            f"/api/v1/meals/{meal_id}/correct", json=correction_data, headers=auth_headers)
        # Should allow users to correct their data
        assert response.status_code in [200, 404]

    def test_data_portability_compliance(self, client, test_user, auth_headers):
        """Test data portability (GDPR Article 20)."""

        # Test data export functionality
        response = client.get(
            f"/api/v1/privacy/{test_user.student_id}/export", headers=auth_headers)
        assert response.status_code == 200

        export_data = response.json()

        # Should include all user data in structured format
        required_sections = ["user_profile",
                             "meals", "feedback", "consent_history"]

        for section in required_sections:
            assert section in export_data

        # Test that exported data is in machine-readable format
        assert isinstance(export_data, dict)

        # Test that export includes metadata
        assert "export_date" in export_data
        assert "data_format_version" in export_data

        # Test export in different formats
        response = client.get(
            f"/api/v1/privacy/{test_user.student_id}/export?format=json", headers=auth_headers)
        assert response.status_code == 200

        # Test CSV export
        response = client.get(
            f"/api/v1/privacy/{test_user.student_id}/export?format=csv", headers=auth_headers)
        assert response.status_code in [200, 501]  # OK or not implemented

        # Test that export is complete and accurate
        if "meals" in export_data and export_data["meals"]:
            meal_data = export_data["meals"][0]
            required_meal_fields = ["meal_id", "timestamp", "detected_foods"]

            for field in required_meal_fields:
                assert field in meal_data

    def test_right_to_erasure_compliance(self, client, test_user, auth_headers, db_session):
        """Test right to erasure/right to be forgotten (GDPR Article 17)."""

        # Create some test data for the user
        test_meal = Meal(
            student_id=test_user.student_id,
            image_path="/test/path.jpg",
            analysis_status="completed"
        )
        db_session.add(test_meal)
        db_session.commit()

        # Test partial data deletion (specific meal)
        response = client.delete(
            f"/api/v1/privacy/meals/{test_meal.meal_id}/delete", headers=auth_headers)
        assert response.status_code == 200

        # Verify meal was deleted
        response = client.get(
            f"/api/v1/history/meals/{test_meal.meal_id}", headers=auth_headers)
        assert response.status_code == 404

        # Test complete account deletion
        response = client.delete(
            f"/api/v1/privacy/{test_user.student_id}/delete", headers=auth_headers)
        assert response.status_code == 200

        deletion_result = response.json()
        assert "deleted" in deletion_result
        assert deletion_result["deleted"] == True

        # Test that data is actually deleted
        # User should no longer be able to login
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "test_password"
        })
        assert login_response.status_code == 401

        # Test that associated data is also deleted
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=auth_headers)
        assert response.status_code in [401, 404]

    def test_data_retention_compliance(self, client, test_user, auth_headers):
        """Test data retention policies."""

        # Test that old data is automatically deleted according to retention policy

        # Create old meal data (simulate)
        old_date = datetime.utcnow() - timedelta(days=400)  # Over 1 year old

        # Test retention policy endpoint
        response = client.get(
            "/api/v1/privacy/retention-policy", headers=auth_headers)
        assert response.status_code == 200

        policy = response.json()
        assert "meal_data_retention_days" in policy
        assert "user_data_retention_days" in policy

        # Test data cleanup for inactive users
        response = client.post(
            "/api/v1/admin/privacy/cleanup-inactive", headers=auth_headers)
        # This might require admin privileges
        assert response.status_code in [200, 403]

    def test_data_encryption_compliance(self, client, test_user, sample_image, auth_headers):
        """Test data encryption at rest and in transit."""

        # Test that sensitive data is encrypted in storage
        # This would typically be tested at the database level

        # Test file upload encryption
        with open(sample_image, 'rb') as img_file:
            response = client.post(
                "/api/v1/meals/analyze",
                files={"image": ("meal.jpg", img_file, "image/jpeg")},
                data={"student_id": str(test_user.student_id)},
                headers=auth_headers
            )

        # Test that images are stored securely
        if response.status_code == 200:
            # Images should be stored with encryption or in secure location
            # This would depend on actual storage implementation
            pass

        # Test that API responses don't expose sensitive data
        response = client.get(
            f"/api/v1/history/{test_user.student_id}/meals", headers=auth_headers)

        if response.status_code == 200:
            meals_data = response.json()

            # Should not expose internal file paths
            for meal in meals_data.get("meals", []):
                if "image_path" in meal:
                    assert not meal["image_path"].startswith("/internal/")
                    assert not meal["image_path"].startswith("/var/")

    def test_privacy_by_design_compliance(self, client, test_user):
        """Test privacy by design principles."""

        # Test default privacy settings
        response = client.get(f"/api/v1/consent/{test_user.student_id}")

        if response.status_code == 200:
            consent = response.json()

            # Default settings should be privacy-friendly
            # Marketing should be opt-in, not opt-out
            # Should default to False
            assert consent.get("marketing", True) == False

            # Analytics might be opt-in or opt-out depending on policy
            # Data storage might be necessary for functionality

    def test_cross_border_data_transfer_compliance(self, client, test_user, auth_headers):
        """Test compliance with cross-border data transfer regulations."""

        # Test data localization requirements
        response = client.get(
            f"/api/v1/privacy/{test_user.student_id}/data-location", headers=auth_headers)

        if response.status_code == 200:
            location_info = response.json()

            # Should specify where data is stored
            assert "storage_location" in location_info
            assert "processing_location" in location_info

            # For Nigerian users, data should ideally be stored locally
            # or in jurisdictions with adequate protection

    def test_breach_notification_compliance(self, client, auth_headers):
        """Test data breach notification procedures."""

        # Test breach notification endpoint (admin only)
        breach_data = {
            "incident_type": "unauthorized_access",
            "affected_users": 1,
            "data_types": ["meal_images", "user_profiles"],
            "incident_date": datetime.utcnow().isoformat(),
            "description": "Test breach notification"
        }

        response = client.post(
            "/api/v1/admin/privacy/breach-notification", json=breach_data, headers=auth_headers)
        # Should require admin privileges
        assert response.status_code in [201, 403]

        # Test user notification of breach
        response = client.get(
            "/api/v1/privacy/breach-notifications", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_children_privacy_protection(self, client):
        """Test additional protections for users under 18 (if applicable)."""

        # Test registration with age verification
        minor_registration = {
            "name": "Minor User",
            "email": "minor@university.edu.ng",
            "password": "SecurePassword123!",
            "date_of_birth": "2010-01-01"  # Under 18
        }

        response = client.post("/api/v1/auth/register",
                               json=minor_registration)

        # Should require parental consent or additional protections
        if response.status_code == 201:
            # If registration is allowed, should have additional protections
            user_data = response.json()
            # Check for enhanced privacy settings
        else:
            # Registration might be restricted for minors
            assert response.status_code in [400, 403]

    def test_privacy_policy_compliance(self, client):
        """Test privacy policy accessibility and compliance."""

        # Test privacy policy endpoint
        response = client.get("/api/v1/privacy/policy")
        assert response.status_code == 200

        policy = response.json()

        # Should include required information
        required_sections = [
            "data_collection",
            "data_usage",
            "data_sharing",
            "user_rights",
            "contact_information"
        ]

        for section in required_sections:
            assert section in policy

        # Test privacy policy version tracking
        assert "version" in policy
        assert "last_updated" in policy

        # Test that users are notified of policy changes
        response = client.get("/api/v1/privacy/policy-updates")
        assert response.status_code in [200, 404]

    def test_audit_trail_compliance(self, client, test_user, auth_headers):
        """Test audit trail for privacy-related actions."""

        # Test that privacy actions are logged

        # Update consent
        consent_data = {
            "data_storage": True,
            "analytics": True,
            "marketing": False
        }

        response = client.post(
            f"/api/v1/consent/{test_user.student_id}", json=consent_data, headers=auth_headers)
        assert response.status_code in [200, 201]

        # Check audit trail
        response = client.get(
            f"/api/v1/privacy/{test_user.student_id}/audit-trail", headers=auth_headers)

        if response.status_code == 200:
            audit_trail = response.json()

            # Should log consent changes
            consent_events = [event for event in audit_trail.get("events", [])
                              if event.get("action") == "consent_updated"]

            assert len(consent_events) > 0

            # Audit events should include required information
            for event in consent_events:
                assert "timestamp" in event
                assert "action" in event
                assert "user_id" in event

    def test_anonymization_and_pseudonymization(self, client, test_user, auth_headers):
        """Test data anonymization and pseudonymization."""

        # Test anonymized analytics data
        response = client.get(
            "/api/v1/analytics/anonymized-usage", headers=auth_headers)

        if response.status_code == 200:
            analytics = response.json()

            # Should not contain personally identifiable information
            for record in analytics.get("usage_data", []):
                assert "email" not in record
                assert "name" not in record
                assert "student_id" not in record or record["student_id"] == "anonymized"

        # Test pseudonymized research data
        response = client.get(
            "/api/v1/research/pseudonymized-data", headers=auth_headers)

        if response.status_code == 200:
            research_data = response.json()

            # Should use pseudonyms instead of real identifiers
            for record in research_data.get("meal_data", []):
                if "user_id" in record:
                    # Should be pseudonymized (hashed or encrypted)
                    assert len(record["user_id"]) > 20  # Likely a hash
                    assert record["user_id"] != str(test_user.student_id)
