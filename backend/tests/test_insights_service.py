"""Tests for insights service functionality."""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.insights_service import insights_service
from app.models.user import Student
from app.models.meal import Meal, DetectedFood
from app.models.feedback import FeedbackRecord
from app.models.history import WeeklyInsight


class TestInsightsService:
    """Test cases for insights service."""

    @pytest.fixture
    def sample_student(self, db_session: Session):
        """Create a sample student with history enabled."""
        student = Student(
            email="insights@example.com",
            name="Insights Student",
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
            email="noinsights@example.com",
            name="No Insights Student",
            password_hash="hashed_password",
            history_enabled=False
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        return student

    @pytest.fixture
    def week_meals_balanced(self, db_session: Session, sample_student: Student):
        """Create a week of balanced meals."""
        meals = []
        week_start = date.today() - timedelta(days=7)

        # Create meals for each day of the week with good variety
        food_groups = ["carbohydrates", "proteins",
                       "vitamins", "minerals", "fats"]

        for day in range(7):
            meal_date = datetime.combine(
                week_start + timedelta(days=day), datetime.min.time())

            # Create 2 meals per day
            for meal_num in range(2):
                meal = Meal(
                    student_id=sample_student.id,
                    image_path=f"/uploads/balanced_meal_{day}_{meal_num}.jpg",
                    upload_date=meal_date +
                    timedelta(hours=meal_num * 6 + 8),  # 8am and 2pm
                    analysis_status="completed"
                )
                db_session.add(meal)
                db_session.flush()

                # Add diverse detected foods
                # 3 food groups per meal
                for i, food_group in enumerate(food_groups[:3]):
                    detected_food = DetectedFood(
                        meal_id=meal.id,
                        food_name=f"{food_group.title()} Food {i}",
                        confidence_score=0.85 + (i * 0.03),
                        food_class=food_group,
                        bounding_box={"x": 10 + i*20, "y": 10,
                                      "width": 100, "height": 100}
                    )
                    db_session.add(detected_food)

                # Add feedback with good balance score
                feedback = FeedbackRecord(
                    meal_id=meal.id,
                    student_id=sample_student.id,
                    feedback_text=f"Balanced meal feedback {day}_{meal_num}",
                    feedback_type="comprehensive_nutrition_analysis",
                    recommendations={
                        "suggestions": ["Keep up the good work!"],
                        "balance_score": 0.8 + (day * 0.02)  # Improving trend
                    }
                )
                db_session.add(feedback)
                meals.append(meal)

        db_session.commit()
        return meals, week_start

    @pytest.fixture
    def week_meals_unbalanced(self, db_session: Session, sample_student: Student):
        """Create a week of unbalanced meals."""
        meals = []
        week_start = date.today() - timedelta(days=14)  # Different week

        for day in range(7):
            meal_date = datetime.combine(
                week_start + timedelta(days=day), datetime.min.time())

            meal = Meal(
                student_id=sample_student.id,
                image_path=f"/uploads/unbalanced_meal_{day}.jpg",
                upload_date=meal_date + timedelta(hours=12),
                analysis_status="completed"
            )
            db_session.add(meal)
            db_session.flush()

            # Add only carbohydrates (unbalanced)
            detected_food = DetectedFood(
                meal_id=meal.id,
                food_name="Rice",
                confidence_score=0.9,
                food_class="carbohydrates",
                bounding_box={"x": 10, "y": 10, "width": 100, "height": 100}
            )
            db_session.add(detected_food)

            # Add feedback with poor balance score
            feedback = FeedbackRecord(
                meal_id=meal.id,
                student_id=sample_student.id,
                feedback_text=f"Unbalanced meal feedback {day}",
                feedback_type="comprehensive_nutrition_analysis",
                recommendations={
                    "suggestions": ["Add more variety to your meals"],
                    "balance_score": 0.3 - (day * 0.02)  # Declining trend
                }
            )
            db_session.add(feedback)
            meals.append(meal)

        db_session.commit()
        return meals, week_start

    @pytest.mark.asyncio
    async def test_generate_weekly_insight_balanced_meals(self, db_session: Session, sample_student: Student, week_meals_balanced):
        """Test generating insights for balanced meals."""
        meals, week_start = week_meals_balanced
        week_end = week_start + timedelta(days=6)

        insight = await insights_service.generate_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            week_end_date=week_end,
            db=db_session
        )

        assert insight is not None
        assert insight.meals_analyzed == 14  # 2 meals per day for 7 days
        assert insight.student_id == sample_student.id
        assert len(insight.positive_trends) > 0
        assert "balanced" in " ".join(insight.positive_trends).lower()

        # Check that insight was stored in database
        stored_insight = db_session.query(WeeklyInsight).filter(
            WeeklyInsight.student_id == sample_student.id,
            WeeklyInsight.week_start_date == week_start
        ).first()
        assert stored_insight is not None

    @pytest.mark.asyncio
    async def test_generate_weekly_insight_unbalanced_meals(self, db_session: Session, sample_student: Student, week_meals_unbalanced):
        """Test generating insights for unbalanced meals."""
        meals, week_start = week_meals_unbalanced
        week_end = week_start + timedelta(days=6)

        insight = await insights_service.generate_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            week_end_date=week_end,
            db=db_session
        )

        assert insight is not None
        assert insight.meals_analyzed == 7  # 1 meal per day for 7 days
        assert len(insight.improvement_areas) > 0

        # Should identify missing food groups
        improvement_text = " ".join(insight.improvement_areas).lower()
        assert any(group in improvement_text for group in [
                   "proteins", "vitamins", "minerals"])

    @pytest.mark.asyncio
    async def test_generate_weekly_insight_no_meals(self, db_session: Session, sample_student: Student):
        """Test generating insights when no meals exist."""
        week_start = date.today() - timedelta(days=21)  # Empty week
        week_end = week_start + timedelta(days=6)

        insight = await insights_service.generate_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            week_end_date=week_end,
            db=db_session
        )

        assert insight is not None
        assert insight.meals_analyzed == 0
        assert "no meals recorded" in insight.recommendations.lower()

    @pytest.mark.asyncio
    async def test_generate_weekly_insight_no_consent(self, db_session: Session, sample_student_no_history: Student):
        """Test generating insights without consent."""
        week_start = date.today() - timedelta(days=7)
        week_end = week_start + timedelta(days=6)

        insight = await insights_service.generate_weekly_insight(
            student_id=sample_student_no_history.id,
            week_start_date=week_start,
            week_end_date=week_end,
            db=db_session
        )

        assert insight is None

    @pytest.mark.asyncio
    async def test_get_existing_weekly_insight(self, db_session: Session, sample_student: Student, week_meals_balanced):
        """Test retrieving existing weekly insight."""
        meals, week_start = week_meals_balanced
        week_end = week_start + timedelta(days=6)

        # Generate initial insight
        initial_insight = await insights_service.generate_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            week_end_date=week_end,
            db=db_session
        )

        # Retrieve the same insight
        retrieved_insight = await insights_service.get_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            db=db_session
        )

        assert retrieved_insight is not None
        assert retrieved_insight.student_id == initial_insight.student_id
        assert retrieved_insight.meals_analyzed == initial_insight.meals_analyzed

    @pytest.mark.asyncio
    async def test_get_trend_analysis_improving(self, db_session: Session, sample_student: Student, week_meals_balanced):
        """Test trend analysis with improving nutrition."""
        meals, week_start = week_meals_balanced

        # Generate insight for the balanced week
        await insights_service.generate_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            week_end_date=week_start + timedelta(days=6),
            db=db_session
        )

        trends = await insights_service.get_trend_analysis(
            student_id=sample_student.id,
            weeks=2,
            db=db_session
        )

        assert "error" not in trends
        assert trends["weeks_analyzed"] >= 1
        assert trends["consistency_score"] > 0
        assert isinstance(trends["recommendations"], list)

    @pytest.mark.asyncio
    async def test_get_trend_analysis_declining(self, db_session: Session, sample_student: Student, week_meals_unbalanced):
        """Test trend analysis with declining nutrition."""
        meals, week_start = week_meals_unbalanced

        # Generate insight for the unbalanced week
        await insights_service.generate_weekly_insight(
            student_id=sample_student.id,
            week_start_date=week_start,
            week_end_date=week_start + timedelta(days=6),
            db=db_session
        )

        trends = await insights_service.get_trend_analysis(
            student_id=sample_student.id,
            weeks=2,
            db=db_session
        )

        assert "error" not in trends
        assert trends["weeks_analyzed"] >= 1
        # Should be low for unbalanced meals
        assert trends["average_balance_score"] < 0.5

    @pytest.mark.asyncio
    async def test_get_trend_analysis_no_consent(self, db_session: Session, sample_student_no_history: Student):
        """Test trend analysis without consent."""
        trends = await insights_service.get_trend_analysis(
            student_id=sample_student_no_history.id,
            weeks=4,
            db=db_session
        )

        assert "error" in trends
        assert trends["error"] == "History not enabled"

    @pytest.mark.asyncio
    async def test_get_trend_analysis_no_data(self, db_session: Session, sample_student: Student):
        """Test trend analysis with no data."""
        trends = await insights_service.get_trend_analysis(
            student_id=sample_student.id,
            weeks=4,
            db=db_session
        )

        assert trends["weeks_analyzed"] == 0
        assert trends["trend_direction"] == "no_data"
        assert "start logging meals" in " ".join(
            trends["recommendations"]).lower()

    def test_food_group_recommendations(self):
        """Test food group specific recommendations."""
        carb_recs = insights_service._get_food_group_recommendations(
            "carbohydrates")
        protein_recs = insights_service._get_food_group_recommendations(
            "proteins")
        vitamin_recs = insights_service._get_food_group_recommendations(
            "vitamins")

        assert len(carb_recs) > 0
        assert any("rice" in rec.lower() or "yam" in rec.lower()
                   for rec in carb_recs)

        assert len(protein_recs) > 0
        assert any("beans" in rec.lower() or "fish" in rec.lower()
                   for rec in protein_recs)

        assert len(vitamin_recs) > 0
        assert any("fruit" in rec.lower() or "orange" in rec.lower()
                   for rec in vitamin_recs)

    def test_trend_direction_calculation(self):
        """Test trend direction calculation logic."""
        # Improving trend
        improving_scores = [0.5, 0.6, 0.7, 0.8]
        trend = insights_service._calculate_trend_direction(improving_scores)
        assert trend == "improving"

        # Declining trend
        declining_scores = [0.8, 0.7, 0.6, 0.5]
        trend = insights_service._calculate_trend_direction(declining_scores)
        assert trend == "declining"

        # Stable trend
        stable_scores = [0.7, 0.68, 0.72, 0.69]
        trend = insights_service._calculate_trend_direction(stable_scores)
        assert trend == "stable"

        # Insufficient data
        insufficient_scores = [0.7]
        trend = insights_service._calculate_trend_direction(
            insufficient_scores)
        assert trend == "insufficient_data"

    def test_trend_recommendations_generation(self):
        """Test trend-based recommendation generation."""
        # Improving trend with good consistency
        recs = insights_service._generate_trend_recommendations(
            "improving", 0.8, [0.7, 0.8])
        assert any("great job" in rec.lower() for rec in recs)
        assert any("excellent" in rec.lower() for rec in recs)

        # Declining trend with poor consistency
        recs = insights_service._generate_trend_recommendations(
            "declining", 0.3, [0.8, 0.6])
        assert any("declining" in rec.lower() for rec in recs)
        assert any("log your meals" in rec.lower() for rec in recs)

        # Stable trend with good balance
        recs = insights_service._generate_trend_recommendations(
            "stable", 0.7, [0.8, 0.8])
        assert any("maintaining" in rec.lower() for rec in recs)

    @pytest.mark.asyncio
    async def test_nutrition_pattern_analysis(self, db_session: Session, sample_student: Student):
        """Test detailed nutrition pattern analysis."""
        # Create a meal with specific pattern
        meal = Meal(
            student_id=sample_student.id,
            image_path="/uploads/pattern_test.jpg",
            upload_date=datetime.utcnow(),
            analysis_status="completed"
        )
        db_session.add(meal)
        db_session.flush()

        # Add foods from different groups
        food_groups = ["carbohydrates", "proteins", "vitamins"]
        for i, food_group in enumerate(food_groups):
            detected_food = DetectedFood(
                meal_id=meal.id,
                food_name=f"Test {food_group}",
                confidence_score=0.9,
                food_class=food_group,
                bounding_box={"x": i*10, "y": 10, "width": 100, "height": 100}
            )
            db_session.add(detected_food)

        # Add feedback
        feedback = FeedbackRecord(
            meal_id=meal.id,
            student_id=sample_student.id,
            feedback_text="Test feedback",
            feedback_type="test",
            recommendations={"balance_score": 0.75}
        )
        db_session.add(feedback)
        db_session.commit()

        # Analyze patterns
        meals = [meal]
        analysis = await insights_service._analyze_nutrition_patterns(meals)

        assert analysis["total_meals"] == 1
        assert len(analysis["food_group_frequencies"]) == 3
        assert analysis["food_group_frequencies"]["carbohydrates"] == 1.0
        assert analysis["overall_balance_score"] == 0.75
        assert analysis["average_daily_variety"] > 0
