#!/usr/bin/env python3
"""
Test script to verify model fields align with Alembic migration schema.
This version doesn't require database connection - it checks model definitions.
"""

from app.models import (
    Base, Student, Meal, DetectedFood, NigerianFood,
    FeedbackRecord, NutritionRule, WeeklyInsight,
    ImageMetadata, ConsentRecord,
    AdminUser, AdminPermission, AdminRolePermission, AdminSession
)


def check_model_columns(model, expected_columns, model_name):
    """Check if model has all expected columns."""
    model_columns = {c.name for c in model.__table__.columns}
    missing = expected_columns - model_columns
    extra = model_columns - expected_columns
    
    if missing:
        print(f"  ✗ {model_name}: Missing columns: {missing}")
        return False
    if extra:
        print(f"  ⚠ {model_name}: Extra columns (may be OK): {extra}")
    
    print(f"  ✓ {model_name}: All expected columns present")
    return True


def check_foreign_keys(model, expected_fks, model_name):
    """Check if model has expected foreign keys."""
    fks = model.__table__.foreign_keys
    fk_tables = {fk.column.table.name for fk in fks}
    
    missing_fks = expected_fks - fk_tables
    if missing_fks:
        print(f"  ✗ {model_name}: Missing foreign keys to: {missing_fks}")
        return False
    
    print(f"  ✓ {model_name}: All foreign keys present")
    return True


def check_indexes(model, expected_indexed_columns, model_name):
    """Check if model has indexes on expected columns."""
    indexed_columns = set()
    for idx in model.__table__.indexes:
        for col in idx.columns:
            indexed_columns.add(col.name)
    
    missing_indexes = expected_indexed_columns - indexed_columns
    if missing_indexes:
        print(f"  ⚠ {model_name}: Missing indexes on: {missing_indexes}")
        # Don't fail on missing indexes, just warn
    else:
        print(f"  ✓ {model_name}: All expected indexes present")
    
    return True


def test_student_model():
    """Test Student model."""
    print("\nTesting Student model...")
    
    expected_columns = {
        'id', 'email', 'name', 'password_hash',
        'registration_date', 'history_enabled',
        'created_at', 'updated_at'
    }
    
    expected_indexed = {'email'}
    
    result = check_model_columns(Student, expected_columns, "Student")
    result &= check_indexes(Student, expected_indexed, "Student")
    
    return result


def test_meal_model():
    """Test Meal model."""
    print("\nTesting Meal model...")
    
    expected_columns = {
        'id', 'student_id', 'image_path', 'upload_date',
        'analysis_status', 'created_at', 'updated_at'
    }
    
    expected_fks = {'students'}
    expected_indexed = {'student_id', 'analysis_status'}
    
    result = check_model_columns(Meal, expected_columns, "Meal")
    result &= check_foreign_keys(Meal, expected_fks, "Meal")
    result &= check_indexes(Meal, expected_indexed, "Meal")
    
    return result


def test_detected_food_model():
    """Test DetectedFood model."""
    print("\nTesting DetectedFood model...")
    
    expected_columns = {
        'id', 'meal_id', 'food_name', 'confidence_score',
        'food_class', 'bounding_box', 'created_at', 'updated_at'
    }
    
    expected_fks = {'meals'}
    expected_indexed = {'meal_id', 'food_class'}
    
    result = check_model_columns(DetectedFood, expected_columns, "DetectedFood")
    result &= check_foreign_keys(DetectedFood, expected_fks, "DetectedFood")
    result &= check_indexes(DetectedFood, expected_indexed, "DetectedFood")
    
    return result


def test_nigerian_food_model():
    """Test NigerianFood model."""
    print("\nTesting NigerianFood model...")
    
    expected_columns = {
        'id', 'food_name', 'local_names', 'food_class',
        'nutritional_info', 'cultural_context',
        'created_at', 'updated_at'
    }
    
    expected_indexed = {'food_name', 'food_class'}
    
    result = check_model_columns(NigerianFood, expected_columns, "NigerianFood")
    result &= check_indexes(NigerianFood, expected_indexed, "NigerianFood")
    
    return result


def test_feedback_record_model():
    """Test FeedbackRecord model."""
    print("\nTesting FeedbackRecord model...")
    
    expected_columns = {
        'id', 'meal_id', 'student_id', 'feedback_text',
        'feedback_type', 'recommendations', 'feedback_date',
        'created_at', 'updated_at'
    }
    
    expected_fks = {'meals', 'students'}
    expected_indexed = {'meal_id', 'student_id', 'feedback_date'}
    
    result = check_model_columns(FeedbackRecord, expected_columns, "FeedbackRecord")
    result &= check_foreign_keys(FeedbackRecord, expected_fks, "FeedbackRecord")
    result &= check_indexes(FeedbackRecord, expected_indexed, "FeedbackRecord")
    
    return result


def test_nutrition_rule_model():
    """Test NutritionRule model."""
    print("\nTesting NutritionRule model...")
    
    expected_columns = {
        'id', 'rule_name', 'condition_logic', 'feedback_template',
        'priority', 'is_active', 'created_at', 'updated_at'
    }
    
    expected_indexed = {'rule_name', 'is_active', 'priority'}
    
    result = check_model_columns(NutritionRule, expected_columns, "NutritionRule")
    result &= check_indexes(NutritionRule, expected_indexed, "NutritionRule")
    
    return result


def test_weekly_insight_model():
    """Test WeeklyInsight model."""
    print("\nTesting WeeklyInsight model...")
    
    expected_columns = {
        'id', 'student_id', 'week_start_date', 'week_end_date',
        'nutrition_summary', 'recommendations', 'generated_at',
        'created_at', 'updated_at'
    }
    
    expected_fks = {'students'}
    expected_indexed = {'student_id', 'week_start_date'}
    
    result = check_model_columns(WeeklyInsight, expected_columns, "WeeklyInsight")
    result &= check_foreign_keys(WeeklyInsight, expected_fks, "WeeklyInsight")
    result &= check_indexes(WeeklyInsight, expected_indexed, "WeeklyInsight")
    
    return result


def test_image_metadata_model():
    """Test ImageMetadata model."""
    print("\nTesting ImageMetadata model...")
    
    expected_columns = {
        'id', 'meal_id', 'file_size', 'file_format',
        'width', 'height', 'quality_score',
        'processing_errors', 'validation_results',
        'created_at', 'updated_at'
    }
    
    expected_fks = {'meals'}
    expected_indexed = {'meal_id'}
    
    result = check_model_columns(ImageMetadata, expected_columns, "ImageMetadata")
    result &= check_foreign_keys(ImageMetadata, expected_fks, "ImageMetadata")
    result &= check_indexes(ImageMetadata, expected_indexed, "ImageMetadata")
    
    return result


def test_consent_record_model():
    """Test ConsentRecord model."""
    print("\nTesting ConsentRecord model...")
    
    expected_columns = {
        'id', 'student_id', 'consent_type', 'consent_given',
        'consent_date', 'consent_version', 'ip_address', 'user_agent',
        'created_at', 'updated_at'
    }
    
    expected_fks = {'students'}
    expected_indexed = {'student_id', 'consent_type', 'consent_date'}
    
    result = check_model_columns(ConsentRecord, expected_columns, "ConsentRecord")
    result &= check_foreign_keys(ConsentRecord, expected_fks, "ConsentRecord")
    result &= check_indexes(ConsentRecord, expected_indexed, "ConsentRecord")
    
    # Check CASCADE delete
    fks = ConsentRecord.__table__.foreign_keys
    student_fk = next((fk for fk in fks if fk.column.table.name == 'students'), None)
    if student_fk and student_fk.ondelete == 'CASCADE':
        print(f"  ✓ ConsentRecord: CASCADE delete configured")
    else:
        print(f"  ⚠ ConsentRecord: CASCADE delete may not be configured")
    
    return result


def test_admin_user_model():
    """Test AdminUser model."""
    print("\nTesting AdminUser model...")
    
    expected_columns = {
        'id', 'email', 'name', 'password_hash',
        'role', 'is_active', 'last_login',
        'created_at', 'updated_at'
    }
    
    expected_indexed = {'email', 'role', 'is_active'}
    
    result = check_model_columns(AdminUser, expected_columns, "AdminUser")
    result &= check_indexes(AdminUser, expected_indexed, "AdminUser")
    
    return result


def test_admin_permission_model():
    """Test AdminPermission model."""
    print("\nTesting AdminPermission model...")
    
    expected_columns = {
        'id', 'name', 'description', 'resource', 'action', 'created_at'
    }
    
    expected_indexed = {'name', 'resource'}
    
    result = check_model_columns(AdminPermission, expected_columns, "AdminPermission")
    result &= check_indexes(AdminPermission, expected_indexed, "AdminPermission")
    
    return result


def test_admin_role_permission_model():
    """Test AdminRolePermission model."""
    print("\nTesting AdminRolePermission model...")
    
    expected_columns = {
        'id', 'role', 'permission_id', 'created_at'
    }
    
    expected_fks = {'admin_permissions'}
    expected_indexed = {'role', 'permission_id'}
    
    result = check_model_columns(AdminRolePermission, expected_columns, "AdminRolePermission")
    result &= check_foreign_keys(AdminRolePermission, expected_fks, "AdminRolePermission")
    result &= check_indexes(AdminRolePermission, expected_indexed, "AdminRolePermission")
    
    return result


def test_admin_session_model():
    """Test AdminSession model."""
    print("\nTesting AdminSession model...")
    
    expected_columns = {
        'id', 'admin_user_id', 'session_token', 'expires_at',
        'is_active', 'ip_address', 'user_agent', 'created_at'
    }
    
    expected_fks = {'admin_users'}
    expected_indexed = {'admin_user_id', 'session_token', 'expires_at', 'is_active'}
    
    result = check_model_columns(AdminSession, expected_columns, "AdminSession")
    result &= check_foreign_keys(AdminSession, expected_fks, "AdminSession")
    result &= check_indexes(AdminSession, expected_indexed, "AdminSession")
    
    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Database Schema Alignment Test (Static)")
    print("=" * 60)
    print("\nVerifying model definitions match Alembic migrations...")
    
    results = []
    
    # Run all tests
    try:
        results.append(("Student", test_student_model()))
        results.append(("Meal", test_meal_model()))
        results.append(("DetectedFood", test_detected_food_model()))
        results.append(("NigerianFood", test_nigerian_food_model()))
        results.append(("FeedbackRecord", test_feedback_record_model()))
        results.append(("NutritionRule", test_nutrition_rule_model()))
        results.append(("WeeklyInsight", test_weekly_insight_model()))
        results.append(("ImageMetadata", test_image_metadata_model()))
        results.append(("ConsentRecord", test_consent_record_model()))
        results.append(("AdminUser", test_admin_user_model()))
        results.append(("AdminPermission", test_admin_permission_model()))
        results.append(("AdminRolePermission", test_admin_role_permission_model()))
        results.append(("AdminSession", test_admin_session_model()))
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
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
        print("✓ All schema alignment tests PASSED")
        print("\nNote: This test verifies model definitions only.")
        print("Database connection tests require running database.")
        exit(0)
    else:
        print("✗ Some schema alignment tests FAILED")
        exit(1)
