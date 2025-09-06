"""Tests for history service functionality."""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.history_service import history_service
from app.models.user import Student
from app.models.meal import Meal, DetectedFood
from app.models.feedback import FeedbackRecord
from app.models.history import MealHistoryRequest


class TestHistoryService:
    """Test cases for history service."""

    @pytest.fixture
    def sample_student(self, db_session: Session):
        """Create a sample student with history enabled."""
        student = Student(
            email="test@example.com",
            name="Test Student",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        return student

    @pytest.fixture
    def sample_student_no_history(self, db_session: Session):
        """Create a sample student with history disabled."""
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
    def sample_meals(self, db_session: Session, sample_student: Student):
        """Create sample meals with detected foods and feedback."""
        meals = []

        # Create meals over the past week
        for i in range(5):
            meal_date = datetime.utcnow() - timedelta(days=i)
            meal = Meal(
                student_id=sample_student.id,
                image_path=f"/uploads/meal_{i}.jpg",
                upload_date=meal_date,
                analysis_status="completed"
            )
            db_session.add(meal)
            db_session.flush()

            # Add detected foods
            detected_food = DetectedFood(
                meal_id=meal.id,
                food_name=f"Nigerian Food {i}",
                confidence_score=0.85 + (i * 0.02),
                food_class="carbohydrates" if i % 2 == 0 else "proteins",
                bounding_box={"x": 10, "y": 10, "width": 100, "height": 100}
            )
            db_session.add(detected_food)

            # Add feedback
            feedback = FeedbackRecord(
                meal_id=meal.id,
                student_id=sample_student.id,
                feedback_text=f"Feedback for meal {i}",
                feedback_type="comprehensive_nutrition_analysis",
                recommendations={
                    "suggestions": [f"Suggestion {i}"],
                    "balance_score": 0.7 + (i * 0.05)
                }
            )
            db_session.add(feedback)
            meals.append(meal)

        db_session.commit()
        return meals

    @pytest.mark.asyncio
    async def test_get_meal_history_with_consent(self, db_session: Session, sample_student: Student, sample_meals):
        """Test getting meal history when student has consent."""
        request = MealHistoryRequest(limit=10, offset=0)

        result = await history_service.get_meal_history(
            student_id=sample_student.id,
            db=db_session,
            request=request
        )

        assert result.total_count == 5
        assert len(result.meals) == 5
        assert not result.has_more

        # Check meal data structure
        meal = result.meals[0]
        assert "meal_id" in meal
        assert "upload_date" in meal
        assert "detected_foods" in meal
        assert "feedback" in meal
        assert len(meal["detected_foods"]) == 1
        assert meal["feedback"] is not None

    @pytest.mark.asyncio
    async def test_get_meal_history_without_consent(self, db_session: Session, sample_student_no_history: Student):
        """Test getting meal history when student has no consent."""
        request = MealHistoryRequest(limit=10, offset=0)

        result = await history_service.get_meal_history(
            student_id=sample_student_no_history.id,
            db=db_session,
            request=request
        )

        assert result.total_count == 0
        assert len(result.meals) == 0
        assert not result.has_more

    @pytest.mark.asyncio
    async def test_get_meal_history_with_date_filters(self, db_session: Session, sample_student: Student, sample_meals):
        """Test meal history with date filtering."""
        # Filter to last 2 days
        start_date = (datetime.utcnow() - timedelta(days=2)).date()
        request = MealHistoryRequest(start_date=start_date, limit=10, offset=0)

        result = await history_service.get_meal_history(
            student_id=sample_student.id,
            db=db_session,
            request=request
        )

        # Should get meals from last 2 days (including today)
        assert result.total_count <= 3
        assert len(result.meals) <= 3

    @pytest.mark.asyncio
    async def test_get_meal_history_pagination(self, db_session: Session, sample_student: Student, sample_meals):
        """Test meal history pagination."""
        # Get first 2 meals
        request = MealHistoryRequest(limit=2, offset=0)
        result = await history_service.get_meal_history(
            student_id=sample_student.id,
            db=db_session,
            request=request
        )

        assert len(result.meals) == 2
        assert result.has_more
        assert result.total_count == 5

        # Get next 2 meals
        request = MealHistoryRequest(limit=2, offset=2)
        result = await history_service.get_meal_history(
            student_id=sample_student.id,
            db=db_session,
            request=request
        )

        assert len(result.meals) == 2
        assert result.has_more

    @pytest.mark.asyncio
    async def test_delete_meal_history_by_ids(self, db_session: Session, sample_student: Student, sample_meals):
        """Test deleting specific meals by ID."""
        meal_ids = [sample_meals[0].id, sample_meals[1].id]

        result = await history_service.delete_meal_history(
            student_id=sample_student.id,
            db=db_session,
            meal_ids=meal_ids
        )

        assert result["deleted_meals"] == 2
        assert result["deleted_feedback"] == 2
        assert result["deleted_detected_foods"] == 2

        # Verify meals are deleted
        remaining_meals = db_session.query(Meal).filter(
            Meal.student_id == sample_student.id
        ).count()
        assert remaining_meals == 3

    @pytest.mark.asyncio
    async def test_delete_meal_history_by_date(self, db_session: Session, sample_student: Student, sample_meals):
        """Test deleting meals before a specific date."""
        # Delete meals older than 2 days
        before_date = (datetime.utcnow() - timedelta(days=2)).date()

        result = await history_service.delete_meal_history(
            student_id=sample_student.id,
            db=db_session,
            before_date=before_date
        )

        # At least 2 meals should be older than 2 days
        assert result["deleted_meals"] >= 2

        # Verify remaining meals are recent
        remaining_meals = db_session.query(Meal).filter(
            Meal.student_id == sample_student.id
        ).all()

        for meal in remaining_meals:
            assert meal.upload_date.date() >= before_date

    @pytest.mark.asyncio
    async def test_delete_all_meal_history(self, db_session: Session, sample_student: Student, sample_meals):
        """Test deleting all meal history."""
        result = await history_service.delete_meal_history(
            student_id=sample_student.id,
            db=db_session
        )

        assert result["deleted_meals"] == 5
        assert result["deleted_feedback"] == 5
        assert result["deleted_detected_foods"] == 5

        # Verify all meals are deleted
        remaining_meals = db_session.query(Meal).filter(
            Meal.student_id == sample_student.id
        ).count()
        assert remaining_meals == 0

    @pytest.mark.asyncio
    async def test_get_nutrition_trends_with_consent(self, db_session: Session, sample_student: Student, sample_meals):
        """Test getting nutrition trends with proper consent."""
        result = await history_service.get_nutrition_trends(
            student_id=sample_student.id,
            db=db_session,
            days=7
        )

        assert "error" not in result
        assert result["total_meals"] == 5
        assert result["period_days"] == 7
        assert "nutrition_frequency" in result
        assert "balance_trend" in result
        assert result["average_balance_score"] > 0

    @pytest.mark.asyncio
    async def test_get_nutrition_trends_without_consent(self, db_session: Session, sample_student_no_history: Student):
        """Test getting nutrition trends without consent."""
        result = await history_service.get_nutrition_trends(
            student_id=sample_student_no_history.id,
            db=db_session,
            days=7
        )

        assert "error" in result
        assert result["error"] == "History not enabled for this student"

    @pytest.mark.asyncio
    async def test_update_history_consent_enable(self, db_session: Session, sample_student_no_history: Student):
        """Test enabling history consent."""
        result = await history_service.update_history_consent(
            student_id=sample_student_no_history.id,
            db=db_session,
            history_enabled=True
        )

        assert result["history_enabled"] is True
        assert result["previous_consent"] is False

        # Verify in database
        db_session.refresh(sample_student_no_history)
        assert sample_student_no_history.history_enabled is True

    @pytest.mark.asyncio
    async def test_update_history_consent_disable(self, db_session: Session, sample_student: Student):
        """Test disabling history consent."""
        result = await history_service.update_history_consent(
            student_id=sample_student.id,
            db=db_session,
            history_enabled=False
        )

        assert result["history_enabled"] is False
        assert result["previous_consent"] is True

        # Verify in database
        db_session.refresh(sample_student)
        assert sample_student.history_enabled is False

    @pytest.mark.asyncio
    async def test_get_meal_statistics_with_consent(self, db_session: Session, sample_student: Student, sample_meals):
        """Test getting meal statistics with consent."""
        result = await history_service.get_meal_statistics(
            student_id=sample_student.id,
            db=db_session
        )

        assert "error" not in result
        assert result["total_meals"] == 5
        assert result["meals_last_7_days"] == 5
        assert result["meals_last_30_days"] == 5
        assert "first_meal_date" in result
        assert "tracking_since" in result

    @pytest.mark.asyncio
    async def test_get_meal_statistics_without_consent(self, db_session: Session, sample_student_no_history: Student):
        """Test getting meal statistics without consent."""
        result = await history_service.get_meal_statistics(
            student_id=sample_student_no_history.id,
            db=db_session
        )

        assert "error" in result
        assert result["error"] == "History not enabled"

    @pytest.mark.asyncio
    async def test_privacy_compliance_cross_student(self, db_session: Session, sample_student: Student, sample_meals):
        """Test that students can only access their own data."""
        # Create another student
        other_student = Student(
            email="other@example.com",
            name="Other Student",
            password_hash="hashed_password",
            history_enabled=True
        )
        db_session.add(other_student)
        db_session.commit()
        db_session.refresh(other_student)

        # Try to get first student's data using second student's ID
        request = MealHistoryRequest(limit=10, offset=0)
        result = await history_service.get_meal_history(
            student_id=other_student.id,
            db=db_session,
            request=request
        )

        # Should return empty results for other student
        assert result.total_count == 0
        assert len(result.meals) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_meals(self, db_session: Session, sample_student: Student):
        """Test deleting meals that don't exist."""
        fake_meal_ids = [uuid4(), uuid4()]

        result = await history_service.delete_meal_history(
            student_id=sample_student.id,
            db=db_session,
            meal_ids=fake_meal_ids
        )

        assert result["deleted_meals"] == 0
        assert "No meals found" in result["message"]
