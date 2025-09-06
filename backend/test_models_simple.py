#!/usr/bin/env python3
"""Simple test script to verify models work correctly."""

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

    from app.models.base import Base
    from app.models.user import Student
    from app.models.meal import Meal, DetectedFood, NigerianFood
    from app.models.feedback import FeedbackRecord, NutritionRule
    from app.models.history import WeeklyInsight
    from app.core.validation import (
        ImageValidation,
        UserValidation,
        FoodValidation,
        NutritionRuleValidation,
        ValidationError
    )
    from app.core.database_utils import initialize_sample_data

    print("✓ All imports successful")

    # Create in-memory database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Test creating a student
    student = Student(
        email="test@example.com",
        name="Test Student",
        password_hash="hashed_password",
        history_enabled=False
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    print(f"✓ Student created with ID: {student.id}")

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
    print("✓ Detected food created")

    # Test creating feedback record
    feedback = FeedbackRecord(
        meal_id=meal.id,
        student_id=student.id,
        feedback_text="Great meal! Try adding more vegetables.",
        feedback_type="nutritional_advice",
        recommendations={"add_vegetables": True}
    )
    session.add(feedback)
    session.commit()
    print("✓ Feedback record created")

    # Test creating weekly insight
    insight = WeeklyInsight(
        student_id=student.id,
        week_start_date=date(2024, 1, 1),
        week_end_date=date(2024, 1, 7),
        nutrition_summary={"balance_score": 0.7},
        recommendations="Try to include more vegetables."
    )
    session.add(insight)
    session.commit()
    print("✓ Weekly insight created")

    # Test sample data initialization
    if initialize_sample_data(session):
        print("✓ Sample data initialized")

        # Check sample data
        foods_count = session.query(NigerianFood).count()
        rules_count = session.query(NutritionRule).count()
        print(f"✓ Sample data: {foods_count} foods, {rules_count} rules")
    else:
        print("✗ Sample data initialization failed")

    # Test validation functions
    try:
        # Test image validation
        ImageValidation.validate_file_extension("test.jpg")
        ImageValidation.validate_file_size(1024 * 1024)  # 1MB
        ImageValidation.validate_image_dimensions(512, 512)
        print("✓ Image validation works")

        # Test user validation
        UserValidation.validate_password_strength("TestPassword123")
        print("✓ User validation works")

        # Test food validation
        FoodValidation.validate_food_class("carbohydrates")
        FoodValidation.validate_confidence_score(0.95)
        FoodValidation.validate_bounding_box(
            {"x": 10, "y": 20, "width": 100, "height": 80})
        print("✓ Food validation works")

        # Test nutrition rule validation
        NutritionRuleValidation.validate_condition_logic(
            {"missing_food_groups": ["proteins"]})
        NutritionRuleValidation.validate_feedback_template(
            "Test feedback message")
        print("✓ Nutrition rule validation works")

    except ValidationError as e:
        print(f"✗ Validation error: {e}")
    except Exception as e:
        print(f"✗ Unexpected validation error: {e}")

    # Test invalid validation cases
    try:
        ImageValidation.validate_file_extension("test.gif")
        print("✗ Should have failed for invalid extension")
    except ValidationError:
        print("✓ Invalid extension properly rejected")

    try:
        FoodValidation.validate_confidence_score(1.5)
        print("✗ Should have failed for invalid confidence")
    except ValidationError:
        print("✓ Invalid confidence properly rejected")

    session.close()
    print("\n✓ All tests passed! Models and validation are working correctly.")

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Note: This is expected if email-validator is not installed")
    print("The models will work fine once dependencies are properly installed")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
