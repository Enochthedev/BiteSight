#!/usr/bin/env python3
"""
Test script to verify all model imports work correctly.
Tests both direct imports and imports from app.models package.
"""

def test_direct_imports():
    """Test importing models directly from their modules."""
    print("Testing direct imports...")
    
    try:
        from app.models.base import Base, TimestampMixin, BaseEntity
        print("✓ Base models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import base models: {e}")
        return False
    
    try:
        from app.models.user import Student, StudentCreate, StudentUpdate, StudentResponse, LoginRequest, LoginResponse
        print("✓ User models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import user models: {e}")
        return False
    
    try:
        from app.models.meal import Meal, DetectedFood, NigerianFood, FoodDetectionResult, MealAnalysis
        print("✓ Meal models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import meal models: {e}")
        return False
    
    try:
        from app.models.feedback import FeedbackRecord, NutritionRule, NutritionFeedback
        print("✓ Feedback models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import feedback models: {e}")
        return False
    
    try:
        from app.models.history import WeeklyInsight, MealHistoryRequest, MealHistoryResponse
        print("✓ History models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import history models: {e}")
        return False
    
    try:
        from app.models.image_metadata import ImageMetadata, ImageMetadataCreate, ImageMetadataResponse
        print("✓ Image metadata models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import image metadata models: {e}")
        return False
    
    try:
        from app.models.consent import ConsentRecord, ConsentRequest, ConsentResponse
        print("✓ Consent models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import consent models: {e}")
        return False
    
    try:
        from app.models.admin import AdminUser, AdminPermission, AdminRolePermission, AdminSession
        print("✓ Admin models imported successfully")
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import admin models: {e}")
        return False
    
    return True


def test_package_imports():
    """Test importing models from app.models package."""
    print("\nTesting package imports...")
    
    try:
        from app.models import (
            Base, TimestampMixin, BaseEntity,
            Student, StudentCreate, StudentUpdate, StudentResponse,
            Meal, DetectedFood, NigerianFood,
            FeedbackRecord, NutritionRule,
            WeeklyInsight,
            ImageMetadata,
            ConsentRecord,
            AdminUser, AdminPermission, AdminRolePermission, AdminSession
        )
        print("✓ All models imported from app.models package successfully")
        return True
    except ModuleNotFoundError as e:
        print(f"✗ Failed to import from app.models: {e}")
        return False
    except ImportError as e:
        print(f"✗ Import error from app.models: {e}")
        return False


def test_model_attributes():
    """Test that imported models have expected attributes."""
    print("\nTesting model attributes...")
    
    try:
        from app.models import Student, Meal, FeedbackRecord
        
        # Check Student has expected attributes
        assert hasattr(Student, '__tablename__'), "Student missing __tablename__"
        assert hasattr(Student, 'id'), "Student missing id"
        assert hasattr(Student, 'email'), "Student missing email"
        print("✓ Student model has expected attributes")
        
        # Check Meal has expected attributes
        assert hasattr(Meal, '__tablename__'), "Meal missing __tablename__"
        assert hasattr(Meal, 'id'), "Meal missing id"
        assert hasattr(Meal, 'student_id'), "Meal missing student_id"
        print("✓ Meal model has expected attributes")
        
        # Check FeedbackRecord has expected attributes
        assert hasattr(FeedbackRecord, '__tablename__'), "FeedbackRecord missing __tablename__"
        assert hasattr(FeedbackRecord, 'id'), "FeedbackRecord missing id"
        assert hasattr(FeedbackRecord, 'meal_id'), "FeedbackRecord missing meal_id"
        print("✓ FeedbackRecord model has expected attributes")
        
        return True
    except AssertionError as e:
        print(f"✗ Attribute check failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error checking attributes: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Model Import Verification Test")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Direct Imports", test_direct_imports()))
    results.append(("Package Imports", test_package_imports()))
    results.append(("Model Attributes", test_model_attributes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All import tests PASSED")
        exit(0)
    else:
        print("✗ Some import tests FAILED")
        exit(1)
