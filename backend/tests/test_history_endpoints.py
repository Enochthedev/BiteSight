"""Tests for history API endpoints."""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import Student
from app.models.meal import Meal, DetectedFood
from app.models.feedback import FeedbackRecord


class TestHistoryEndpoints:
    """Test cases for history API endpoints."""

    @pytest.fixture
    def authenticated_student(self, db_session: Session, test_client: TestClient):
        """Create an authenticated student with history enabled."""
        student = Student(
            email="history@example.com",
            name="History Student",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        # Mock authentication by setting the student in the dependency
        return student

    @pytest.fixture
    def student_no_history(self, db_session: Session):
        """Create a student with history disabled."""
        student = Student(
            email="nohistory@example.com",
            name="No History Student",
            password_hash="hashed_password",
            history_enabled=False
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        return student

    @pytest.fixture
    def sample_meals_data(self, db_session: Session, authenticated_student: Student):
        """Create sample meals for testing."""
        meals = []

        for i in range(3):
            meal_date = datetime.utcnow() - timedelta(days=i)
            meal = Meal(
                student_id=authenticated_student.id,
                image_path=f"/uploads/test_meal_{i}.jpg",
                upload_date=meal_date,
                analysis_status="completed"
            )
            db_session.add(meal)
            db_session.flush()

            # Add detected food
            detected_food = DetectedFood(
                meal_id=meal.id,
                food_name=f"Test Food {i}",
                confidence_score=0.9,
                food_class="carbohydrates",
                bounding_box={"x": 0, "y": 0, "width": 100, "height": 100}
            )
            db_session.add(detected_food)

            # Add feedback
            feedback = FeedbackRecord(
                meal_id=meal.id,
                student_id=authenticated_student.id,
                feedback_text=f"Test feedback {i}",
                feedback_type="test",
                recommendations={"suggestions": [
                    f"Test suggestion {i}"], "balance_score": 0.8}
            )
            db_session.add(feedback)
            meals.append(meal)

        db_session.commit()
        return meals

    def test_get_meal_history_success(self, test_client: TestClient, authenticated_student: Student, sample_meals_data):
        """Test successful meal history retrieval."""
        # Mock the authentication dependency
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        response = test_client.get("/api/v1/history/meals")

        assert response.status_code == 200
        data = response.json()

        assert "meals" in data
        assert "total_count" in data
        assert "has_more" in data
        assert data["total_count"] == 3
        assert len(data["meals"]) == 3

        # Check meal structure
        meal = data["meals"][0]
        assert "meal_id" in meal
        assert "upload_date" in meal
        assert "detected_foods" in meal
        assert "feedback" in meal

    def test_get_meal_history_with_filters(self, test_client: TestClient, authenticated_student: Student, sample_meals_data):
        """Test meal history with date filters."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        # Filter to today only
        today = date.today()
        response = test_client.get(
            f"/api/v1/history/meals?start_date={today}&end_date={today}")

        assert response.status_code == 200
        data = response.json()

        # Should get at most 1 meal (today's meal)
        assert data["total_count"] <= 1

    def test_get_meal_history_pagination(self, test_client: TestClient, authenticated_student: Student, sample_meals_data):
        """Test meal history pagination."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        # Get first page
        response = test_client.get("/api/v1/history/meals?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["meals"]) == 2
        assert data["has_more"] is True
        assert data["total_count"] == 3

    def test_get_meal_statistics_success(self, test_client: TestClient, authenticated_student: Student, sample_meals_data):
        """Test successful meal statistics retrieval."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        response = test_client.get("/api/v1/history/statistics")

        assert response.status_code == 200
        data = response.json()

        assert "total_meals" in data
        assert "meals_last_7_days" in data
        assert "meals_last_30_days" in data
        assert data["total_meals"] == 3

    def test_get_nutrition_trends_success(self, test_client: TestClient, authenticated_student: Student, sample_meals_data):
        """Test successful nutrition trends retrieval."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        response = test_client.get("/api/v1/history/trends?days=7")

        assert response.status_code == 200
        data = response.json()

        assert "total_meals" in data
        assert "nutrition_frequency" in data
        assert "balance_trend" in data
        assert data["total_meals"] == 3

    def test_delete_meal_history_by_date(self, test_client: TestClient, authenticated_student: Student, sample_meals_data):
        """Test deleting meal history by date."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        # Delete meals older than today
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = test_client.delete(
            f"/api/v1/history/meals?before_date={yesterday}")

        assert response.status_code == 200
        data = response.json()

        assert "deleted_meals" in data
        assert data["deleted_meals"] >= 1

    def test_delete_meal_history_validation_error(self, test_client: TestClient, authenticated_student: Student):
        """Test delete meal history without criteria."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        # Try to delete without any criteria
        response = test_client.delete("/api/v1/history/meals")

        assert response.status_code == 400
        assert "Must specify either meal_ids or before_date" in response.json()[
            "detail"]

    def test_update_history_consent_enable(self, test_client: TestClient, student_no_history: Student):
        """Test enabling history consent."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: student_no_history

        response = test_client.put(
            "/api/v1/history/consent?history_enabled=true")

        assert response.status_code == 200
        data = response.json()

        assert data["history_enabled"] is True
        assert data["previous_consent"] is False

    def test_update_history_consent_disable(self, test_client: TestClient, authenticated_student: Student):
        """Test disabling history consent."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        response = test_client.put(
            "/api/v1/history/consent?history_enabled=false")

        assert response.status_code == 200
        data = response.json()

        assert data["history_enabled"] is False
        assert data["previous_consent"] is True

    def test_access_without_consent(self, test_client: TestClient, student_no_history: Student):
        """Test accessing history endpoints without consent."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: student_no_history

        # Try to get meal history
        response = test_client.get("/api/v1/history/meals")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0  # Should return empty results

        # Try to get statistics
        response = test_client.get("/api/v1/history/statistics")
        assert response.status_code == 403

        # Try to get trends
        response = test_client.get("/api/v1/history/trends")
        assert response.status_code == 403

    def test_invalid_date_format(self, test_client: TestClient, authenticated_student: Student):
        """Test invalid date format in query parameters."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        response = test_client.get(
            "/api/v1/history/meals?start_date=invalid-date")

        assert response.status_code == 422  # Validation error

    def test_invalid_pagination_parameters(self, test_client: TestClient, authenticated_student: Student):
        """Test invalid pagination parameters."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        # Negative offset
        response = test_client.get("/api/v1/history/meals?offset=-1")
        assert response.status_code == 422

        # Limit too high
        response = test_client.get("/api/v1/history/meals?limit=200")
        assert response.status_code == 422

        # Limit too low
        response = test_client.get("/api/v1/history/meals?limit=0")
        assert response.status_code == 422

    def test_trends_invalid_days_parameter(self, test_client: TestClient, authenticated_student: Student):
        """Test invalid days parameter for trends."""
        from app.core.dependencies import get_current_student
        test_client.app.dependency_overrides[get_current_student] = lambda: authenticated_student

        # Days too high
        response = test_client.get("/api/v1/history/trends?days=400")
        assert response.status_code == 422

        # Days too low
        response = test_client.get("/api/v1/history/trends?days=0")
        assert response.status_code == 422
