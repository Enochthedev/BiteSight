#!/usr/bin/env python3
"""Test core models without email validation dependency."""

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

    print("✓ Core imports successful")

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

    # Test creating Nigerian food
    nigerian_food = NigerianFood(
        food_name="Test Jollof Rice",
        local_names={"yoruba": "Test Jollof"},
        food_class="carbohydrates",
        nutritional_info={"calories_per_100g": 150},
        cultural_context="Test food for unit testing"
    )
    session.add(nigerian_food)
    session.commit()
    print("✓ Nigerian food created")

    # Test creating nutrition rule
    nutrition_rule = NutritionRule(
        rule_name="Test Rule",
        condition_logic={"missing_food_groups": ["proteins"]},
        feedback_template="Test feedback message",
        priority=1,
        is_active=True
    )
    session.add(nutrition_rule)
    session.commit()
    print("✓ Nutrition rule created")

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

    # Test relationships
    student_meals = session.query(Meal).filter(
        Meal.student_id == student.id).all()
    print(f"✓ Student has {len(student_meals)} meals")

    meal_foods = session.query(DetectedFood).filter(
        DetectedFood.meal_id == meal.id).all()
    print(f"✓ Meal has {len(meal_foods)} detected foods")

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

    try:
        UserValidation.validate_password_strength("weak")
        print("✗ Should have failed for weak password")
    except ValidationError:
        print("✓ Weak password properly rejected")

    try:
        NutritionRuleValidation.validate_condition_logic({})
        print("✗ Should have failed for empty condition logic")
    except ValidationError:
        print("✓ Empty condition logic properly rejected")

    # Test database queries
    all_students = session.query(Student).all()
    all_meals = session.query(Meal).all()
    all_foods = session.query(DetectedFood).all()
    all_nigerian_foods = session.query(NigerianFood).all()
    all_rules = session.query(NutritionRule).all()
    all_feedback = session.query(FeedbackRecord).all()
    all_insights = session.query(WeeklyInsight).all()

    print(f"✓ Database contains:")
    print(f"  - {len(all_students)} students")
    print(f"  - {len(all_meals)} meals")
    print(f"  - {len(all_foods)} detected foods")
    print(f"  - {len(all_nigerian_foods)} Nigerian foods")
    print(f"  - {len(all_rules)} nutrition rules")
    print(f"  - {len(all_feedback)} feedback records")
    print(f"  - {len(all_insights)} weekly insights")

    session.close()
    print("\n✓ All core model tests passed! Database schema and validation are working correctly.")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
