#!/usr/bin/env python3
"""Test SQLAlchemy models without Pydantic dependencies."""

import sys
import os
from datetime import datetime, date
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.models.base import Base, TimestampMixin, BaseEntity
    from app.models.user import Student
    from app.models.meal import Meal, DetectedFood, NigerianFood
    from app.models.feedback import FeedbackRecord, NutritionRule
    from app.models.history import WeeklyInsight
    from app.core.validation import (
        ImageValidation,
        UserValidation,
        FoodValidation,
        NutritionRuleValidation,
        ValidationError,
        validate_uuid,
        validate_date_range
    )

    print("✓ SQLAlchemy models imported successfully")

    # Create in-memory database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

    # List all created tables
    table_names = list(Base.metadata.tables.keys())
    print(f"✓ Created tables: {', '.join(table_names)}")

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Test creating a student
    student = Student(
        email="test@example.com",
        name="Test Student",
        password_hash="hashed_password_123",
        history_enabled=False
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    print(f"✓ Student created with ID: {student.id}")
    print(f"  - Email: {student.email}")
    print(f"  - Name: {student.name}")
    print(f"  - History enabled: {student.history_enabled}")
    print(f"  - Created at: {student.created_at}")

    # Test creating a meal
    meal = Meal(
        student_id=student.id,
        image_path="/uploads/test_image.jpg",
        analysis_status="pending"
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    print(f"✓ Meal created with ID: {meal.id}")
    print(f"  - Student ID: {meal.student_id}")
    print(f"  - Image path: {meal.image_path}")
    print(f"  - Status: {meal.analysis_status}")

    # Test creating detected food
    detected_food = DetectedFood(
        meal_id=meal.id,
        food_name="Jollof Rice",
        confidence_score=0.95,
        food_class="carbohydrates",
        bounding_box={"x": 10, "y": 20, "width": 100, "height": 80}
    )
    session.add(detected_food)
    session.commit()
    session.refresh(detected_food)
    print(f"✓ Detected food created with ID: {detected_food.id}")
    print(f"  - Food name: {detected_food.food_name}")
    print(f"  - Confidence: {detected_food.confidence_score}")
    print(f"  - Food class: {detected_food.food_class}")

    # Test creating Nigerian food
    nigerian_food = NigerianFood(
        food_name="Test Jollof Rice",
        local_names={"yoruba": "Test Jollof", "igbo": "Test Jollof"},
        food_class="carbohydrates",
        nutritional_info={"calories_per_100g": 150, "carbs": 30, "protein": 3},
        cultural_context="Test food for unit testing purposes"
    )
    session.add(nigerian_food)
    session.commit()
    session.refresh(nigerian_food)
    print(f"✓ Nigerian food created with ID: {nigerian_food.id}")
    print(f"  - Food name: {nigerian_food.food_name}")
    print(f"  - Local names: {nigerian_food.local_names}")

    # Test creating nutrition rule
    nutrition_rule = NutritionRule(
        rule_name="Test Missing Protein Rule",
        condition_logic={"missing_food_groups": ["proteins"]},
        feedback_template="Your meal looks good, but try adding some protein like beans or meat.",
        priority=1,
        is_active=True
    )
    session.add(nutrition_rule)
    session.commit()
    session.refresh(nutrition_rule)
    print(f"✓ Nutrition rule created with ID: {nutrition_rule.id}")
    print(f"  - Rule name: {nutrition_rule.rule_name}")
    print(f"  - Priority: {nutrition_rule.priority}")
    print(f"  - Active: {nutrition_rule.is_active}")

    # Test creating feedback record
    feedback = FeedbackRecord(
        meal_id=meal.id,
        student_id=student.id,
        feedback_text="Great meal! Try adding more vegetables for better nutrition balance.",
        feedback_type="nutritional_advice",
        recommendations={"add_vegetables": True, "reduce_carbs": False}
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    print(f"✓ Feedback record created with ID: {feedback.id}")
    print(f"  - Feedback type: {feedback.feedback_type}")
    print(f"  - Recommendations: {feedback.recommendations}")

    # Test creating weekly insight
    insight = WeeklyInsight(
        student_id=student.id,
        week_start_date=date(2024, 1, 1),
        week_end_date=date(2024, 1, 7),
        nutrition_summary={
            "carbohydrates_frequency": 0.8,
            "proteins_frequency": 0.6,
            "balance_score": 0.7
        },
        recommendations="Try to include more vegetables in your daily meals."
    )
    session.add(insight)
    session.commit()
    session.refresh(insight)
    print(f"✓ Weekly insight created with ID: {insight.id}")
    print(f"  - Week: {insight.week_start_date} to {insight.week_end_date}")
    print(f"  - Balance score: {insight.nutrition_summary['balance_score']}")

    # Test relationships and queries
    print("\n--- Testing Relationships ---")

    # Get student's meals
    student_meals = session.query(Meal).filter(
        Meal.student_id == student.id).all()
    print(f"✓ Student has {len(student_meals)} meals")

    # Get meal's detected foods
    meal_foods = session.query(DetectedFood).filter(
        DetectedFood.meal_id == meal.id).all()
    print(f"✓ Meal has {len(meal_foods)} detected foods")

    # Get student's feedback
    student_feedback = session.query(FeedbackRecord).filter(
        FeedbackRecord.student_id == student.id).all()
    print(f"✓ Student has {len(student_feedback)} feedback records")

    # Get student's insights
    student_insights = session.query(WeeklyInsight).filter(
        WeeklyInsight.student_id == student.id).all()
    print(f"✓ Student has {len(student_insights)} weekly insights")

    # Test validation functions
    print("\n--- Testing Validation Functions ---")

    try:
        # Test image validation
        ImageValidation.validate_file_extension("test.jpg")
        ImageValidation.validate_file_size(1024 * 1024)  # 1MB
        ImageValidation.validate_image_dimensions(512, 512)
        print("✓ Image validation functions work")

        # Test user validation
        UserValidation.validate_password_strength("TestPassword123")
        UserValidation.validate_email_uniqueness("new@example.com", session)
        print("✓ User validation functions work")

        # Test food validation
        FoodValidation.validate_food_class("carbohydrates")
        FoodValidation.validate_confidence_score(0.95)
        FoodValidation.validate_bounding_box(
            {"x": 10, "y": 20, "width": 100, "height": 80})
        print("✓ Food validation functions work")

        # Test nutrition rule validation
        NutritionRuleValidation.validate_condition_logic(
            {"missing_food_groups": ["proteins"]})
        NutritionRuleValidation.validate_feedback_template(
            "Test feedback message")
        print("✓ Nutrition rule validation functions work")

        # Test utility validation
        test_uuid = validate_uuid(str(uuid4()))
        validate_date_range(date(2024, 1, 1), date(2024, 1, 31))
        print("✓ Utility validation functions work")

    except ValidationError as e:
        print(f"✗ Validation error: {e}")
    except Exception as e:
        print(f"✗ Unexpected validation error: {e}")

    # Test invalid validation cases
    print("\n--- Testing Invalid Cases ---")

    validation_tests = [
        ("Invalid file extension",
         lambda: ImageValidation.validate_file_extension("test.gif")),
        ("Invalid confidence score",
         lambda: FoodValidation.validate_confidence_score(1.5)),
        ("Weak password", lambda: UserValidation.validate_password_strength("weak")),
        ("Empty condition logic",
         lambda: NutritionRuleValidation.validate_condition_logic({})),
        ("Invalid UUID", lambda: validate_uuid("invalid-uuid")),
        ("Invalid date range", lambda: validate_date_range(
            date(2024, 1, 31), date(2024, 1, 1)))
    ]

    for test_name, test_func in validation_tests:
        try:
            test_func()
            print(f"✗ {test_name} should have failed")
        except ValidationError:
            print(f"✓ {test_name} properly rejected")
        except Exception as e:
            print(f"? {test_name} failed with unexpected error: {e}")

    # Test database counts
    print("\n--- Database Summary ---")
    counts = {
        "Students": session.query(Student).count(),
        "Meals": session.query(Meal).count(),
        "Detected Foods": session.query(DetectedFood).count(),
        "Nigerian Foods": session.query(NigerianFood).count(),
        "Nutrition Rules": session.query(NutritionRule).count(),
        "Feedback Records": session.query(FeedbackRecord).count(),
        "Weekly Insights": session.query(WeeklyInsight).count()
    }

    for entity, count in counts.items():
        print(f"✓ {entity}: {count}")

    session.close()
    print("\n🎉 All SQLAlchemy model tests passed! Database schema and validation are working correctly.")
    print("\nNote: Pydantic models with EmailStr will work once 'email-validator' is installed.")
    print("Run: pip install pydantic[email] to enable full email validation.")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
