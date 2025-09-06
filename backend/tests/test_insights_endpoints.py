"""Tests for insights API endpoints."""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import Student
from app.models.meal import Meal, DetectedFood
from app.models.feedback import FeedbackRecord


class TestInsightsEndpoints:
    """Test cases for insights API endpoints."""

    @pytest.fixture
    def authenticated_student(self, db_session: Session):
        """Create an authenticated student with history enabled."""
        student = Student(
            email="insights_api@example.com",
            name="Insights API Student",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        return student

    @pytest.fixture
    def student_no_history(self, db_session: Session):
        """Create a student with history disabled."""
        student = Student(
            email="no_insights_api@example.com",
            name="No Insights API Student",
            password_hash="hashed_password",
            history_enabled=False
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        return student

    @pytest.fixture
    def sample_week_data(self, db_session: Session, authenticated_student: Student):
        """Create sample data for a week."""
        week_start = date.today() - timedelta(days=7)
        meals = []

        for day in range(7):
            meal_date = datetime.combine(
                week_start + timedelta(days=day), datetime.min.time())

            meal = Meal(
                student_id=authenticated_student.id,
                image_path=f"/uploads/api_test_meal_{day}.jpg",
                upload_date=meal_date + timedelta(hours=12),
                analysis_status="completed"
            )
            db_session.add(meal)
            db_session.flush()

            # Add detected foods
            food_groups = ["carbohydrates", "proteins", "vitamins"]
            for i, food_group in enumerate(food_groups):
                detected_food = DetectedFood(
                    meal_id=meal.id,
                    food_name=f"API Test {food_group} {day}",
                    confidence_score=0.85,
                    food_class=food_group,
                    bounding_box={"x": i*10, "y": 10,
                                  "width": 100, "height": 100}
                )
                db_session.add(detected_food)

            # Add feedback
            feedback = FeedbackRecord(
                meal_id=meal.id,
                student_id=authenticated_student.id,
                feedback_text=f"API test feedback {day}",
                feedback_type="test",
                recommendations={
                    "suggestions": [f"Test suggestion {day}"],
                    "balance_score": 0.7 + (day * 0.02)
                }
            )
            db_session.add(feedback)
            meals.append(meal)

        db_session.commit()
        return meals, week_start

    def test_get_weekly_insights_success(self, test_client: TestClient, authenticated_student: Student, sample_week_data):
        """Test successful weekly insights retrieval."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        meals, week_start = sample_week_data

        response = test_client.get(
            f"/api/v1/history/insights/weekly?week_start_date={week_start}")

        assert response.status_code == 200
        data = response.json()

        assert "student_id" in data
        assert "week_period" in data
        assert "meals_analyzed" in data
        assert "nutrition_balance" in data
        assert "improvement_areas" in data
        assert "positive_trends" in data
        assert "recommendations" in data
        assert data["meals_analyzed"] == 7

    def test_get_weekly_insights_no_data(self, test_client: TestClient, authenticated_student: Student):
        """Test weekly insights with no data."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        # Use a week with no data
        empty_week = date.today() - timedelta(days=21)

        response = test_client.get(
            f"/api/v1/history/insights/weekly?week_start_date={empty_week}")

        assert response.status_code == 200
        data = response.json()

        assert data["meals_analyzed"] == 0
        assert "no meals recorded" in data["recommendations"].lower()

    def test_get_weekly_insights_no_consent(self, test_client: TestClient, student_no_history: Student):
        """Test weekly insights without consent."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: student_no_history

        week_start = date.today() - timedelta(days=7)

        response = test_client.get(
            f"/api/v1/history/insights/weekly?week_start_date={week_start}")

        assert response.status_code == 403
        assert "history not enabled" in response.json()["detail"].lower()

    def test_generate_weekly_insights_success(self, test_client: TestClient, authenticated_student: Student, sample_week_data):
        """Test generating new weekly insights."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        meals, week_start = sample_week_data
        week_end = week_start + timedelta(days=6)

        response = test_client.post(
            f"/api/v1/history/insights/weekly/generate?week_start_date={week_start}&week_end_date={week_end}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["meals_analyzed"] == 7
        assert data["student_id"] == str(authenticated_student.id)

    def test_generate_weekly_insights_invalid_date_range(self, test_client: TestClient, authenticated_student: Student):
        """Test generating insights with invalid date range."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        week_start = date.today()
        week_end = week_start - timedelta(days=1)  # End before start

        response = test_client.post(
            f"/api/v1/history/insights/weekly/generate?week_start_date={week_start}&week_end_date={week_end}"
        )

        assert response.status_code == 400
        assert "end date must be after start date" in response.json()[
            "detail"].lower()

    def test_generate_weekly_insights_too_long_period(self, test_client: TestClient, authenticated_student: Student):
        """Test generating insights with period longer than 7 days."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        week_start = date.today() - timedelta(days=10)
        week_end = week_start + timedelta(days=10)  # 10 days period

        response = test_client.post(
            f"/api/v1/history/insights/weekly/generate?week_start_date={week_start}&week_end_date={week_end}"
        )

        assert response.status_code == 400
        assert "cannot exceed 7 days" in response.json()["detail"].lower()

    def test_get_nutrition_trend_analysis_success(self, test_client: TestClient, authenticated_student: Student, sample_week_data):
        """Test successful nutrition trend analysis."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        # First generate some insights
        meals, week_start = sample_week_data
        week_end = week_start + timedelta(days=6)

        # Generate insight first
        test_client.post(
            f"/api/v1/history/insights/weekly/generate?week_start_date={week_start}&week_end_date={week_end}"
        )

        # Now get trends
        response = test_client.get("/api/v1/history/insights/trends?weeks=2")

        assert response.status_code == 200
        data = response.json()

        assert "weeks_analyzed" in data
        assert "trend_direction" in data
        assert "consistency_score" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_get_nutrition_trend_analysis_no_consent(self, test_client: TestClient, student_no_history: Student):
        """Test trend analysis without consent."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: student_no_history

        response = test_client.get("/api/v1/history/insights/trends?weeks=4")

        assert response.status_code == 403
        assert "history not enabled" in response.json()["detail"].lower()

    def test_get_nutrition_trend_analysis_no_data(self, test_client: TestClient, authenticated_student: Student):
        """Test trend analysis with no data."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        response = test_client.get("/api/v1/history/insights/trends?weeks=4")

        assert response.status_code == 200
        data = response.json()

        assert data["weeks_analyzed"] == 0
        assert data["trend_direction"] == "no_data"

    def test_invalid_week_start_date_format(self, test_client: TestClient, authenticated_student: Student):
        """Test invalid date format in weekly insights."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        response = test_client.get(
            "/api/v1/history/insights/weekly?week_start_date=invalid-date")

        assert response.status_code == 422  # Validation error

    def test_invalid_weeks_parameter(self, test_client: TestClient, authenticated_student: Student):
        """Test invalid weeks parameter for trend analysis."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        # Weeks too high
        response = test_client.get("/api/v1/history/insights/trends?weeks=15")
        assert response.status_code == 422

        # Weeks too low
        response = test_client.get("/api/v1/history/insights/trends?weeks=0")
        assert response.status_code == 422

    def test_missing_required_week_start_date(self, test_client: TestClient, authenticated_student: Student):
        """Test missing required week_start_date parameter."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        response = test_client.get("/api/v1/history/insights/weekly")

        assert response.status_code == 422  # Missing required parameter

    def test_weekly_insights_response_structure(self, test_client: TestClient, authenticated_student: Student, sample_week_data):
        """Test the structure of weekly insights response."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        meals, week_start = sample_week_data

        response = test_client.get(
            f"/api/v1/history/insights/weekly?week_start_date={week_start}")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = [
            "student_id", "week_period", "meals_analyzed",
            "nutrition_balance", "improvement_areas",
            "positive_trends", "recommendations", "generated_at"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check data types
        assert isinstance(data["meals_analyzed"], int)
        assert isinstance(data["nutrition_balance"], dict)
        assert isinstance(data["improvement_areas"], list)
        assert isinstance(data["positive_trends"], list)
        assert isinstance(data["recommendations"], str)

    def test_trend_analysis_response_structure(self, test_client: TestClient, authenticated_student: Student):
        """Test the structure of trend analysis response."""
        from app.core.dependencies import get_current_active_user
        test_client.app.dependency_overrides[get_current_active_user] = lambda: authenticated_student

        response = test_client.get("/api/v1/history/insights/trends?weeks=4")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = [
            "weeks_analyzed", "trend_direction",
            "consistency_score", "recommendations"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check data types
        assert isinstance(data["weeks_analyzed"], int)
        assert isinstance(data["trend_direction"], str)
        assert isinstance(data["consistency_score"], (int, float))
        assert isinstance(data["recommendations"], list)
