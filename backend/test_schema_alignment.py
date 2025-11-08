#!/usr/bin/env python3
"""
Test script to verify model fields align with Alembic migration schema.
Checks foreign keys, indexes, and cascade delete rules.
"""

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models import (
    Base, Student, Meal, DetectedFood, NigerianFood,
    FeedbackRecord, NutritionRule, WeeklyInsight,
    ImageMetadata, ConsentRecord,
    AdminUser, AdminPermission, AdminRolePermission, AdminSession
)


def get_table_columns(table_name):
    """Get column information for a table."""
    inspector = inspect(engine)
    return {col['name']: col for col in inspector.get_columns(table_name)}


def get_table_foreign_keys(table_name):
    """Get foreign key information for a table."""
    inspector = inspect(engine)
    return inspector.get_foreign_keys(table_name)


def get_table_indexes(table_name):
    """Get index information for a table."""
    inspector = inspect(engine)
    return inspector.get_indexes(table_name)


def test_student_model():
    """Test Student model alignment with students table."""
    print("Testing Student model...")
    
    model = Student
    table_name = 'students'
    
    # Expected columns from migration
    expected_columns = {
        'id', 'email', 'name', 'password_hash',
        'registration_date', 'history_enabled',
        'created_at', 'updated_at'
    }
    
    # Get model columns
    model_columns = set(c.name for c in model.__table__.columns)
    
    # Check all expected columns exist
    missing = expected_columns - model_columns
    extra = model_columns - expected_columns
    
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    if extra:
        print(f"  ⚠ Extra columns: {extra}")
    
    # Check indexes
    indexes = get_table_indexes(table_name)
    index_columns = set()
    for idx in indexes:
        index_columns.update(idx['column_names'])
    
    if 'email' not in index_columns:
        print(f"  ✗ Missing index on email")
        return False
    
    print("  ✓ Student model aligned with schema")
    return True


def test_meal_model():
    """Test Meal model alignment with meals table."""
    print("Testing Meal model...")
    
    model = Meal
    table_name = 'meals'
    
    expected_columns = {
        'id', 'student_id', 'image_path', 'upload_date',
        'analysis_status', 'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to students
    fks = get_table_foreign_keys(table_name)
    has_student_fk = any(fk['referred_table'] == 'students' for fk in fks)
    
    if not has_student_fk:
        print(f"  ✗ Missing foreign key to students")
        return False
    
    # Check indexes
    indexes = get_table_indexes(table_name)
    index_columns = set()
    for idx in indexes:
        index_columns.update(idx['column_names'])
    
    if 'student_id' not in index_columns:
        print(f"  ✗ Missing index on student_id")
        return False
    
    print("  ✓ Meal model aligned with schema")
    return True


def test_detected_food_model():
    """Test DetectedFood model alignment with detected_foods table."""
    print("Testing DetectedFood model...")
    
    model = DetectedFood
    table_name = 'detected_foods'
    
    expected_columns = {
        'id', 'meal_id', 'food_name', 'confidence_score',
        'food_class', 'bounding_box', 'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to meals
    fks = get_table_foreign_keys(table_name)
    has_meal_fk = any(fk['referred_table'] == 'meals' for fk in fks)
    
    if not has_meal_fk:
        print(f"  ✗ Missing foreign key to meals")
        return False
    
    print("  ✓ DetectedFood model aligned with schema")
    return True


def test_nigerian_food_model():
    """Test NigerianFood model alignment with nigerian_foods table."""
    print("Testing NigerianFood model...")
    
    model = NigerianFood
    table_name = 'nigerian_foods'
    
    expected_columns = {
        'id', 'food_name', 'local_names', 'food_class',
        'nutritional_info', 'cultural_context',
        'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    print("  ✓ NigerianFood model aligned with schema")
    return True


def test_feedback_record_model():
    """Test FeedbackRecord model alignment with feedback_records table."""
    print("Testing FeedbackRecord model...")
    
    model = FeedbackRecord
    table_name = 'feedback_records'
    
    expected_columns = {
        'id', 'meal_id', 'student_id', 'feedback_text',
        'feedback_type', 'recommendations', 'feedback_date',
        'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign keys
    fks = get_table_foreign_keys(table_name)
    fk_tables = {fk['referred_table'] for fk in fks}
    
    if 'meals' not in fk_tables:
        print(f"  ✗ Missing foreign key to meals")
        return False
    if 'students' not in fk_tables:
        print(f"  ✗ Missing foreign key to students")
        return False
    
    print("  ✓ FeedbackRecord model aligned with schema")
    return True


def test_nutrition_rule_model():
    """Test NutritionRule model alignment with nutrition_rules table."""
    print("Testing NutritionRule model...")
    
    model = NutritionRule
    table_name = 'nutrition_rules'
    
    expected_columns = {
        'id', 'rule_name', 'condition_logic', 'feedback_template',
        'priority', 'is_active', 'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    print("  ✓ NutritionRule model aligned with schema")
    return True


def test_weekly_insight_model():
    """Test WeeklyInsight model alignment with weekly_insights table."""
    print("Testing WeeklyInsight model...")
    
    model = WeeklyInsight
    table_name = 'weekly_insights'
    
    expected_columns = {
        'id', 'student_id', 'week_start_date', 'week_end_date',
        'nutrition_summary', 'recommendations', 'generated_at',
        'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to students
    fks = get_table_foreign_keys(table_name)
    has_student_fk = any(fk['referred_table'] == 'students' for fk in fks)
    
    if not has_student_fk:
        print(f"  ✗ Missing foreign key to students")
        return False
    
    print("  ✓ WeeklyInsight model aligned with schema")
    return True


def test_image_metadata_model():
    """Test ImageMetadata model alignment with image_metadata table."""
    print("Testing ImageMetadata model...")
    
    model = ImageMetadata
    table_name = 'image_metadata'
    
    expected_columns = {
        'id', 'meal_id', 'file_size', 'file_format',
        'width', 'height', 'quality_score',
        'processing_errors', 'validation_results',
        'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to meals
    fks = get_table_foreign_keys(table_name)
    has_meal_fk = any(fk['referred_table'] == 'meals' for fk in fks)
    
    if not has_meal_fk:
        print(f"  ✗ Missing foreign key to meals")
        return False
    
    print("  ✓ ImageMetadata model aligned with schema")
    return True


def test_consent_record_model():
    """Test ConsentRecord model alignment with consent_records table."""
    print("Testing ConsentRecord model...")
    
    model = ConsentRecord
    table_name = 'consent_records'
    
    expected_columns = {
        'id', 'student_id', 'consent_type', 'consent_given',
        'consent_date', 'consent_version', 'ip_address', 'user_agent',
        'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to students with CASCADE delete
    fks = get_table_foreign_keys(table_name)
    student_fk = next((fk for fk in fks if fk['referred_table'] == 'students'), None)
    
    if not student_fk:
        print(f"  ✗ Missing foreign key to students")
        return False
    
    if student_fk.get('options', {}).get('ondelete') != 'CASCADE':
        print(f"  ⚠ Foreign key should have CASCADE delete")
    
    print("  ✓ ConsentRecord model aligned with schema")
    return True


def test_admin_user_model():
    """Test AdminUser model alignment with admin_users table."""
    print("Testing AdminUser model...")
    
    model = AdminUser
    table_name = 'admin_users'
    
    expected_columns = {
        'id', 'email', 'name', 'password_hash',
        'role', 'is_active', 'last_login',
        'created_at', 'updated_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check indexes
    indexes = get_table_indexes(table_name)
    index_columns = set()
    for idx in indexes:
        index_columns.update(idx['column_names'])
    
    if 'email' not in index_columns:
        print(f"  ✗ Missing index on email")
        return False
    
    print("  ✓ AdminUser model aligned with schema")
    return True


def test_admin_permission_model():
    """Test AdminPermission model alignment with admin_permissions table."""
    print("Testing AdminPermission model...")
    
    model = AdminPermission
    table_name = 'admin_permissions'
    
    expected_columns = {
        'id', 'name', 'description', 'resource', 'action', 'created_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    print("  ✓ AdminPermission model aligned with schema")
    return True


def test_admin_role_permission_model():
    """Test AdminRolePermission model alignment with admin_role_permissions table."""
    print("Testing AdminRolePermission model...")
    
    model = AdminRolePermission
    table_name = 'admin_role_permissions'
    
    expected_columns = {
        'id', 'role', 'permission_id', 'created_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to admin_permissions
    fks = get_table_foreign_keys(table_name)
    has_permission_fk = any(fk['referred_table'] == 'admin_permissions' for fk in fks)
    
    if not has_permission_fk:
        print(f"  ✗ Missing foreign key to admin_permissions")
        return False
    
    print("  ✓ AdminRolePermission model aligned with schema")
    return True


def test_admin_session_model():
    """Test AdminSession model alignment with admin_sessions table."""
    print("Testing AdminSession model...")
    
    model = AdminSession
    table_name = 'admin_sessions'
    
    expected_columns = {
        'id', 'admin_user_id', 'session_token', 'expires_at',
        'is_active', 'ip_address', 'user_agent', 'created_at'
    }
    
    model_columns = set(c.name for c in model.__table__.columns)
    
    missing = expected_columns - model_columns
    if missing:
        print(f"  ✗ Missing columns: {missing}")
        return False
    
    # Check foreign key to admin_users
    fks = get_table_foreign_keys(table_name)
    has_admin_fk = any(fk['referred_table'] == 'admin_users' for fk in fks)
    
    if not has_admin_fk:
        print(f"  ✗ Missing foreign key to admin_users")
        return False
    
    print("  ✓ AdminSession model aligned with schema")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Database Schema Alignment Test")
    print("=" * 60)
    
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
        exit(0)
    else:
        print("✗ Some schema alignment tests FAILED")
        exit(1)
