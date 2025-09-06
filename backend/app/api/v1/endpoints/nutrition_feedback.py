"""Nutrition feedback API endpoints."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.feedback import (
    FeedbackResponse,
    NutritionFeedback,
    NutritionRuleCreate,
    NutritionRuleUpdate,
    NutritionRuleResponse
)
from app.services.feedback_service import feedback_service
from app.services.nutrition_rule_service import nutrition_rule_service
from app.services.analysis_service import analysis_service
from app.models.meal import FoodDetectionResult

router = APIRouter()


@router.post("/generate/{meal_id}", response_model=NutritionFeedback)
async def generate_meal_feedback(
    meal_id: UUID,
    student_id: UUID,
    detected_foods: List[Dict[str, Any]],
    cultural_context: str = "nigerian_general",
    db: Session = Depends(get_db)
):
    """Generate nutrition feedback for a meal."""

    try:
        # Convert detected foods to FoodDetectionResult objects
        food_results = []
        for food_data in detected_foods:
            food_result = FoodDetectionResult(
                food_name=food_data.get("food_name", ""),
                confidence=food_data.get("confidence", 0.0),
                food_class=food_data.get("food_class", ""),
                bounding_box=food_data.get("bounding_box")
            )
            food_results.append(food_result)

        # Generate feedback
        feedback = await feedback_service.generate_feedback(
            meal_id=meal_id,
            student_id=student_id,
            detected_foods=food_results,
            db=db,
            cultural_context=cultural_context
        )

        return feedback

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating feedback: {str(e)}"
        )


@router.get("/history/{student_id}", response_model=List[FeedbackResponse])
async def get_feedback_history(
    student_id: UUID,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get feedback history for a student."""

    try:
        feedback_records = await feedback_service.get_feedback_history(
            student_id=student_id,
            db=db,
            limit=limit
        )

        return [
            FeedbackResponse(
                id=record.id,
                meal_id=record.meal_id,
                student_id=record.student_id,
                feedback_text=record.feedback_text,
                feedback_type=record.feedback_type,
                recommendations=record.recommendations,
                feedback_date=record.feedback_date,
                created_at=record.created_at,
                updated_at=record.updated_at
            )
            for record in feedback_records
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving feedback history: {str(e)}"
        )


@router.get("/meal/{meal_id}", response_model=Optional[FeedbackResponse])
async def get_meal_feedback(
    meal_id: UUID,
    db: Session = Depends(get_db)
):
    """Get feedback for a specific meal."""

    try:
        feedback_record = await feedback_service.get_feedback_by_meal(
            meal_id=meal_id,
            db=db
        )

        if not feedback_record:
            return None

        return FeedbackResponse(
            id=feedback_record.id,
            meal_id=feedback_record.meal_id,
            student_id=feedback_record.student_id,
            feedback_text=feedback_record.feedback_text,
            feedback_type=feedback_record.feedback_type,
            recommendations=feedback_record.recommendations,
            feedback_date=feedback_record.feedback_date,
            created_at=feedback_record.created_at,
            updated_at=feedback_record.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving meal feedback: {str(e)}"
        )


@router.get("/trends/{student_id}")
async def get_nutrition_trends(
    student_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get nutrition trends for a student."""

    try:
        trends = await feedback_service.get_student_nutrition_trends(
            student_id=student_id,
            db=db,
            days=days
        )

        return trends

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving nutrition trends: {str(e)}"
        )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update existing feedback."""

    try:
        updated_record = await feedback_service.update_feedback(
            feedback_id=feedback_id,
            updated_data=update_data,
            db=db
        )

        if not updated_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback record not found"
            )

        return FeedbackResponse(
            id=updated_record.id,
            meal_id=updated_record.meal_id,
            student_id=updated_record.student_id,
            feedback_text=updated_record.feedback_text,
            feedback_type=updated_record.feedback_type,
            recommendations=updated_record.recommendations,
            feedback_date=updated_record.feedback_date,
            created_at=updated_record.created_at,
            updated_at=updated_record.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating feedback: {str(e)}"
        )


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete feedback record."""

    try:
        deleted = await feedback_service.delete_feedback(
            feedback_id=feedback_id,
            db=db
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback record not found"
            )

        return {"message": "Feedback deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting feedback: {str(e)}"
        )


# Nutrition Rules Management Endpoints

@router.post("/rules", response_model=NutritionRuleResponse)
async def create_nutrition_rule(
    rule_data: NutritionRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new nutrition rule."""

    try:
        rule = await nutrition_rule_service.create_rule(rule_data, db)
        return rule

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating nutrition rule: {str(e)}"
        )


@router.get("/rules", response_model=List[NutritionRuleResponse])
async def get_nutrition_rules(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all nutrition rules."""

    try:
        rules = await nutrition_rule_service.get_all_rules(db, active_only)
        return rules

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving nutrition rules: {str(e)}"
        )


@router.get("/rules/{rule_id}", response_model=NutritionRuleResponse)
async def get_nutrition_rule(
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific nutrition rule."""

    try:
        rule = await nutrition_rule_service.get_rule(rule_id, db)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition rule not found"
            )

        return rule

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving nutrition rule: {str(e)}"
        )


@router.put("/rules/{rule_id}", response_model=NutritionRuleResponse)
async def update_nutrition_rule(
    rule_id: UUID,
    rule_data: NutritionRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update a nutrition rule."""

    try:
        updated_rule = await nutrition_rule_service.update_rule(rule_id, rule_data, db)

        if not updated_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition rule not found"
            )

        return updated_rule

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating nutrition rule: {str(e)}"
        )


@router.delete("/rules/{rule_id}")
async def delete_nutrition_rule(
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a nutrition rule."""

    try:
        deleted = await nutrition_rule_service.delete_rule(rule_id, db)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nutrition rule not found"
            )

        return {"message": "Nutrition rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting nutrition rule: {str(e)}"
        )
