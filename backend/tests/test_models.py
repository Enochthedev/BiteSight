"""Tests for database models."""

import pytest
from datetime import datetime, date
from uuid import uuid4

from app.models.user import Student, StudentCreate, StudentUpdate, LoginRequest
from app.models.meal import Meal, DetectedFood, NigerianFood, MealUploadRequest, FoodDetectionResult
from app.models.feedback import FeedbackRecord, NutritionRule, NutritionFeedback
from app.models.history import WeeklyInsight, MealHistoryRequest, NutritionSummary


class TestStudentModel:
    """Test Student model and related Pydantic models."""

    def test_create_student(self, db_session, sample_student_data):
        """Test creating a student in the database."""
        student = Student(
            email=sample_student_data["email"],
            name=sample_student_data["name"],
            password_hash="hashed_password",
            history_enabled=False
        )

        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        assert student.id is not None
        assert student.email == sample_student_data["email"]
        assert student.name == sample_student_data["name"]
        assert student.history_enabled is False
        assert student.created_at is not None
        assert student.registration_date is not None

    def test_student_create_validation(self, sample_student_data):
        """Test StudentCreate Pydantic model validation."""
        # Valid data
        student_create = StudentCreate(**sample_student_data)
        assert student_create.email == sample_student_data["email"]
        assert student_create.name == sample_student_data["name"]

        # Invalid email
        with pytest.raises(ValueError):
            StudentCreate(
                email="invalid-email",
                name="Test Name",
                password="TestPassword123"
            )

        # Short password
        with pytest.raises(ValueError):
            StudentCreate(
                email="test@example.com",
                name="Test Name",
                password="short"
            )

        # Empty name
        with pytest.raises(ValueError):
            StudentCreate(
                email="test@example.com",
                name="",
                password="TestPassword123"
            )

    def test_student_update_validation(self):
        """Test StudentUpdate Pydantic model validation."""
        # Valid partial update
        student_update = StudentUpdate(name="New Name")
        assert student_update.name == "New Name"
        assert student_update.history_enabled is None

        # Valid full update
        student_update = StudentUpdate(
            name="New Name",
            history_enabled=True
        )
        assert student_update.name == "New Name"
        assert student_update.history_enabled is True

        # Empty name should fail
        with pytest.raises(ValueError):
            StudentUpdate(name="")

    def test_login_request_validation(self):
        """Test LoginRequest Pydantic model validation."""
        # Valid login request
        login_request = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert login_request.email == "test@example.com"
        assert login_request.password == "password123"

        # Invalid email
        with pytest.raises(ValueError):
            LoginRequest(email="invalid-email", password="password123")


class TestMealModel:
    """Test Meal and related models."""

    def test_create_meal(self, db_session, sample_student_data):
        """Test creating a meal in the database."""
        # First create a student
        student = Student(
            email=sample_student_data["email"],
            name=sample_student_data["name"],
            password_hash="hashed_password"
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        # Create meal
        meal = Meal(
            student_id=student.id,
            image_path="/uploads/test_image.jpg",
            analysis_status="pending"
        )

        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        assert meal.id is not None
        assert meal.student_id == student.id
        assert meal.image_path == "/uploads/test_image.jpg"
        assert meal.analysis_status == "pending"
        assert meal.upload_date is not None

    def test_create_detected_food(self, db_session, sample_student_data):
        """Test creating detected food in the database."""
        # Create student and meal first
        student = Student(
            email=sample_student_data["email"],
            name=sample_student_data["name"],
            password_hash="hashed_password"
        )
        db_session.add(student)
        db_session.commit()

        meal = Meal(
            student_id=student.id,
            image_path="/uploads/test_image.jpg"
        )
        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        # Create detected food
        detected_food = DetectedFood(
            meal_id=meal.id,
            food_name="Jollof Rice",
            confidence_score=0.95,
            food_class="carbohydrates",
            bounding_box={"x": 10, "y": 20, "width": 100, "height": 80}
        )

        db_session.add(detected_food)
        db_session.commit()
        db_session.refresh(detected_food)

        assert detected_food.id is not None
        assert detected_food.meal_id == meal.id
        assert detected_food.food_name == "Jollof Rice"
        assert float(detected_food.confidence_score) == 0.95
        assert detected_food.food_class == "carbohydrates"
        assert detected_food.bounding_box == {
            "x": 10, "y": 20, "width": 100, "height": 80}

    def test_nigerian_food_model(self, db_session, sample_nigerian_food_data):
        """Test NigerianFood model."""
        nigerian_food = NigerianFood(**sample_nigerian_food_data)

        db_session.add(nigerian_food)
        db_session.commit()
        db_session.refresh(nigerian_food)

        assert nigerian_food.id is not None
        assert nigerian_food.food_name == sample_nigerian_food_data["food_name"]
        assert nigerian_food.food_class == sample_nigerian_food_data["food_class"]
        assert nigerian_food.local_names == sample_nigerian_food_data["local_names"]

    def test_food_detection_result_validation(self):
        """Test FoodDetectionResult Pydantic model validation."""
        # Valid detection result
        result = FoodDetectionResult(
            food_name="Jollof Rice",
            confidence=0.95,
            food_class="carbohydrates",
            bounding_box={"x": 10.0, "y": 20.0, "width": 100.0, "height": 80.0}
        )
        assert result.food_name == "Jollof Rice"
        assert result.confidence == 0.95

        # Invalid confidence (too high)
        with pytest.raises(ValueError):
            FoodDetectionResult(
                food_name="Test Food",
                confidence=1.5,
                food_class="carbohydrates"
            )

        # Invalid confidence (negative)
        with pytest.raises(ValueError):
            FoodDetectionResult(
                food_name="Test Food",
                confidence=-0.1,
                food_class="carbohydrates"
            )

    def test_meal_upload_request_validation(self):
        """Test MealUploadRequest Pydantic model validation."""
        student_id = uuid4()

        # Valid request
        request = MealUploadRequest(student_id=student_id)
        assert request.student_id == student_id
        assert isinstance(request.timestamp, datetime)

        # Valid request with custom timestamp
        custom_time = datetime.now()
        request = MealUploadRequest(
            student_id=student_id,
            timestamp=custom_time
        )
        assert request.timestamp == custom_time


class TestFeedbackModel:
    """Test Feedback and NutritionRule models."""

    def test_create_feedback_record(self, db_session, sample_student_data):
        """Test creating feedback record in the database."""
        # Create student and meal first
        student = Student(
            email=sample_student_data["email"],
            name=sample_student_data["name"],
            password_hash="hashed_password"
        )
        db_session.add(student)
        db_session.commit()

        meal = Meal(
            student_id=student.id,
            image_path="/uploads/test_image.jpg"
        )
        db_session.add(meal)
        db_session.commit()
        db_session.refresh(meal)

        # Create feedback record
        feedback = FeedbackRecord(
            meal_id=meal.id,
            student_id=student.id,
            feedback_text="Great meal! Try adding more vegetables.",
            feedback_type="nutritional_advice",
            recommendations={"add_vegetables": True, "reduce_carbs": False}
        )

        db_session.add(feedback)
        db_session.commit()
        db_session.refresh(feedback)

        assert feedback.id is not None
        assert feedback.meal_id == meal.id
        assert feedback.student_id == student.id
        assert feedback.feedback_text == "Great meal! Try adding more vegetables."
        assert feedback.feedback_type == "nutritional_advice"
        assert feedback.recommendations == {
            "add_vegetables": True, "reduce_carbs": False}

    def test_create_nutrition_rule(self, db_session, sample_nutrition_rule_data):
        """Test creating nutrition rule in the database."""
        rule = NutritionRule(**sample_nutrition_rule_data)

        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)

        assert rule.id is not None
        assert rule.rule_name == sample_nutrition_rule_data["rule_name"]
        assert rule.condition_logic == sample_nutrition_rule_data["condition_logic"]
        assert rule.feedback_template == sample_nutrition_rule_data["feedback_template"]
        assert rule.priority == sample_nutrition_rule_data["priority"]
        assert rule.is_active == sample_nutrition_rule_data["is_active"]

    def test_nutrition_feedback_validation(self):
        """Test NutritionFeedback Pydantic model validation."""
        meal_id = uuid4()

        # Valid feedback
        feedback = NutritionFeedback(
            meal_id=meal_id,
            detected_foods=[{"food_name": "Rice", "confidence": 0.9}],
            missing_food_groups=["proteins"],
            recommendations=["Add beans or meat"],
            overall_balance_score=0.7,
            feedback_message="Good meal, add protein!"
        )

        assert feedback.meal_id == meal_id
        assert feedback.overall_balance_score == 0.7
        assert len(feedback.missing_food_groups) == 1

        # Invalid balance score (too high)
        with pytest.raises(ValueError):
            NutritionFeedback(
                meal_id=meal_id,
                detected_foods=[],
                missing_food_groups=[],
                recommendations=[],
                overall_balance_score=1.5,
                feedback_message="Test"
            )


class TestHistoryModel:
    """Test WeeklyInsight and history-related models."""

    def test_create_weekly_insight(self, db_session, sample_student_data):
        """Test creating weekly insight in the database."""
        # Create student first
        student = Student(
            email=sample_student_data["email"],
            name=sample_student_data["name"],
            password_hash="hashed_password"
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        # Create weekly insight
        insight = WeeklyInsight(
            student_id=student.id,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            nutrition_summary={
                "carbohydrates_frequency": 0.8,
                "proteins_frequency": 0.6,
                "balance_score": 0.7
            },
            recommendations="Try to include more vegetables in your meals."
        )

        db_session.add(insight)
        db_session.commit()
        db_session.refresh(insight)

        assert insight.id is not None
        assert insight.student_id == student.id
        assert insight.week_start_date == date(2024, 1, 1)
        assert insight.week_end_date == date(2024, 1, 7)
        assert insight.nutrition_summary["balance_score"] == 0.7

    def test_meal_history_request_validation(self):
        """Test MealHistoryRequest Pydantic model validation."""
        # Valid request with defaults
        request = MealHistoryRequest()
        assert request.limit == 50
        assert request.offset == 0
        assert request.start_date is None

        # Valid request with custom values
        request = MealHistoryRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            limit=100,
            offset=10
        )
        assert request.start_date == date(2024, 1, 1)
        assert request.end_date == date(2024, 1, 31)
        assert request.limit == 100
        assert request.offset == 10

        # Invalid limit (too high)
        with pytest.raises(ValueError):
            MealHistoryRequest(limit=200)

        # Invalid offset (negative)
        with pytest.raises(ValueError):
            MealHistoryRequest(offset=-1)

    def test_nutrition_summary_validation(self):
        """Test NutritionSummary Pydantic model validation."""
        # Valid summary
        summary = NutritionSummary(
            carbohydrates_frequency=0.8,
            proteins_frequency=0.6,
            fats_frequency=0.4,
            vitamins_frequency=0.7,
            minerals_frequency=0.5,
            water_frequency=0.9,
            balance_score=0.65
        )

        assert summary.carbohydrates_frequency == 0.8
        assert summary.balance_score == 0.65

        # Invalid frequency (too high)
        with pytest.raises(ValueError):
            NutritionSummary(
                carbohydrates_frequency=1.5,
                proteins_frequency=0.6,
                fats_frequency=0.4,
                vitamins_frequency=0.7,
                minerals_frequency=0.5,
                water_frequency=0.9,
                balance_score=0.65
            )

        # Invalid frequency (negative)
        with pytest.raises(ValueError):
            NutritionSummary(
                carbohydrates_frequency=0.8,
                proteins_frequency=-0.1,
                fats_frequency=0.4,
                vitamins_frequency=0.7,
                minerals_frequency=0.5,
                water_frequency=0.9,
                balance_score=0.65
            )
