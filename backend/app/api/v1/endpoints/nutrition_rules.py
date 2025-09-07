"""Nutrition rules management endpoints."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.admin_dependencies import (
    require_nutrition_rules_management, require_nutritionist_or_admin
)
from app.models.admin import AdminUser
from app.models.feedback import (
    NutritionRule, NutritionRuleCreate, NutritionRuleUpdate, NutritionRuleResponse
)
from app.services.nutrition_rules_service import NutritionRulesService

router = APIRouter()


@router.post("/rules", response_model=NutritionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_nutrition_rule(
    rule_data: NutritionRuleCreate,
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Create a new nutrition rule."""
    rules_service = NutritionRulesService(db)

    try:
        rule = rules_service.create_rule(rule_data)
        return NutritionRuleResponse(
            id=rule.id,
            rule_name=rule.rule_name,
            condition_logic=rule.condition_logic,
            feedback_template=rule.feedback_template,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create nutrition rule"
        )


@router.get("/rules", response_model=List[NutritionRuleResponse])
async def list_nutrition_rules(
    active_only: bool = Query(
        False, description="Filter to active rules only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """List nutrition rules with optional filtering."""
    rules_service = NutritionRulesService(db)

    rules, total_count = rules_service.list_rules(
        active_only=active_only,
        skip=skip,
        limit=limit
    )

    return [
        NutritionRuleResponse(
            id=rule.id,
            rule_name=rule.rule_name,
            condition_logic=rule.condition_logic,
            feedback_template=rule.feedback_template,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        for rule in rules
    ]


@router.get("/rules/search", response_model=List[NutritionRuleResponse])
async def search_nutrition_rules(
    query: Optional[str] = Query(
        None, description="Search term for rule name or template"),
    active_only: bool = Query(
        False, description="Filter to active rules only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Number of records to return"),
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Search nutrition rules by name or template content."""
    rules_service = NutritionRulesService(db)

    rules, total_count = rules_service.search_rules(
        query_text=query,
        active_only=active_only,
        skip=skip,
        limit=limit
    )

    return [
        NutritionRuleResponse(
            id=rule.id,
            rule_name=rule.rule_name,
            condition_logic=rule.condition_logic,
            feedback_template=rule.feedback_template,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        for rule in rules
    ]


@router.get("/rules/{rule_id}", response_model=NutritionRuleResponse)
async def get_nutrition_rule(
    rule_id: UUID,
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Get nutrition rule by ID."""
    rules_service = NutritionRulesService(db)

    rule = rules_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition rule not found"
        )

    return NutritionRuleResponse(
        id=rule.id,
        rule_name=rule.rule_name,
        condition_logic=rule.condition_logic,
        feedback_template=rule.feedback_template,
        priority=rule.priority,
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.put("/rules/{rule_id}", response_model=NutritionRuleResponse)
async def update_nutrition_rule(
    rule_id: UUID,
    rule_data: NutritionRuleUpdate,
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Update nutrition rule."""
    rules_service = NutritionRulesService(db)

    try:
        updated_rule = rules_service.update_rule(rule_id, rule_data)
        if not updated_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition rule not found"
            )

        return NutritionRuleResponse(
            id=updated_rule.id,
            rule_name=updated_rule.rule_name,
            condition_logic=updated_rule.condition_logic,
            feedback_template=updated_rule.feedback_template,
            priority=updated_rule.priority,
            is_active=updated_rule.is_active,
            created_at=updated_rule.created_at,
            updated_at=updated_rule.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update nutrition rule"
        )


@router.delete("/rules/{rule_id}")
async def delete_nutrition_rule(
    rule_id: UUID,
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Delete nutrition rule."""
    rules_service = NutritionRulesService(db)

    success = rules_service.delete_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition rule not found"
        )

    return {"message": "Nutrition rule successfully deleted"}


@router.post("/rules/{rule_id}/activate")
async def activate_nutrition_rule(
    rule_id: UUID,
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Activate a nutrition rule."""
    rules_service = NutritionRulesService(db)

    success = rules_service.activate_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition rule not found"
        )

    return {"message": "Nutrition rule activated successfully"}


@router.post("/rules/{rule_id}/deactivate")
async def deactivate_nutrition_rule(
    rule_id: UUID,
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Deactivate a nutrition rule."""
    rules_service = NutritionRulesService(db)

    success = rules_service.deactivate_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition rule not found"
        )

    return {"message": "Nutrition rule deactivated successfully"}


@router.put("/rules/{rule_id}/priority")
async def update_rule_priority(
    rule_id: UUID,
    new_priority: int = Query(..., ge=1, description="New priority value"),
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Update rule priority."""
    rules_service = NutritionRulesService(db)

    success = rules_service.update_rule_priority(rule_id, new_priority)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition rule not found"
        )

    return {"message": f"Rule priority updated to {new_priority}"}


@router.post("/rules/{rule_id}/test")
async def test_nutrition_rule(
    rule_id: UUID,
    test_data: Dict[str, Any],
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Test a nutrition rule against provided data."""
    rules_service = NutritionRulesService(db)

    try:
        result = rules_service.test_rule_condition(rule_id, test_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test nutrition rule"
        )


@router.post("/rules/{rule_id}/duplicate", response_model=NutritionRuleResponse)
async def duplicate_nutrition_rule(
    rule_id: UUID,
    new_name: str = Query(..., description="Name for the duplicated rule"),
    current_admin: AdminUser = Depends(require_nutrition_rules_management),
    db: Session = Depends(get_db)
):
    """Duplicate an existing nutrition rule."""
    rules_service = NutritionRulesService(db)

    try:
        duplicated_rule = rules_service.duplicate_rule(rule_id, new_name)
        return NutritionRuleResponse(
            id=duplicated_rule.id,
            rule_name=duplicated_rule.rule_name,
            condition_logic=duplicated_rule.condition_logic,
            feedback_template=duplicated_rule.feedback_template,
            priority=duplicated_rule.priority,
            is_active=duplicated_rule.is_active,
            created_at=duplicated_rule.created_at,
            updated_at=duplicated_rule.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to duplicate nutrition rule"
        )


@router.get("/rules/active/priority-order", response_model=List[NutritionRuleResponse])
async def get_active_rules_by_priority(
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Get all active rules ordered by priority."""
    rules_service = NutritionRulesService(db)

    rules = rules_service.get_active_rules_by_priority()

    return [
        NutritionRuleResponse(
            id=rule.id,
            rule_name=rule.rule_name,
            condition_logic=rule.condition_logic,
            feedback_template=rule.feedback_template,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        for rule in rules
    ]


@router.post("/rules/validate/condition")
async def validate_rule_condition(
    condition_logic: Dict[str, Any],
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Validate rule condition logic."""
    rules_service = NutritionRulesService(db)

    try:
        errors = rules_service.validate_rule_condition(condition_logic)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate rule condition"
        )


@router.post("/rules/validate/template")
async def validate_feedback_template(
    template: str,
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Validate feedback template."""
    rules_service = NutritionRulesService(db)

    try:
        errors = rules_service.validate_feedback_template(template)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate feedback template"
        )


@router.get("/statistics")
async def get_rules_statistics(
    current_admin: AdminUser = Depends(require_nutritionist_or_admin),
    db: Session = Depends(get_db)
):
    """Get statistics about nutrition rules."""
    rules_service = NutritionRulesService(db)

    try:
        stats = rules_service.get_rules_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rules statistics"
        )
