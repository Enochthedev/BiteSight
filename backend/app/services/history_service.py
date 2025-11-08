"""History service for meal tracking and insights generation."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func, extract
import logging

from app.models.meal import Meal, DetectedFood
from app.models.feedback import FeedbackRecord
from app.models.user import Student
from app.models.history import (
    WeeklyInsight,
    MealHistoryRequest,
    MealHistoryResponse,
    InsightGenerationRequest,
    NutritionSummary,
    WeeklyInsightResponse
)
from app.core.database import get_db

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing meal history and generating insights."""

    def __init__(self):
        pass

    async def get_meal_history(
        self,
        student_id: UUID,
        db: Session,
        request: MealHistoryRequest
    ) -> MealHistoryResponse:
        """Get paginated meal history for a student with privacy checks."""

        # Check if student has history enabled
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.history_enabled:
            return MealHistoryResponse(
                meals=[],
                total_count=0,
                has_more=False,
                limit=request.limit,
                offset=request.offset
            )

        # Build query with filters
        query = db.query(Meal).filter(Meal.student_id == student_id)

        # Apply date filters if provided
        if request.start_date:
            query = query.filter(Meal.upload_date >= request.start_date)
        if request.end_date:
            # Add one day to include the entire end date
            end_datetime = datetime.combine(
                request.end_date, datetime.max.time())
            query = query.filter(Meal.upload_date <= end_datetime)

        # Get total count for pagination
        total_count = query.count()

        # Apply pagination and ordering
        meals = query.options(
            joinedload(Meal.detected_foods),
            joinedload(Meal.feedback_records)
        ).order_by(desc(Meal.upload_date)).offset(request.offset).limit(request.limit).all()

        # Convert to response format
        meal_data = []
        for meal in meals:
            # Get the most recent feedback for this meal
            feedback = None
            if meal.feedback_records:
                feedback = max(meal.feedback_records,
                               key=lambda f: f.feedback_date)

            meal_info = {
                "meal_id": str(meal.id),
                "upload_date": meal.upload_date.isoformat(),
                "analysis_status": meal.analysis_status,
                "image_path": meal.image_path,
                "detected_foods": [
                    {
                        "food_name": food.food_name,
                        "confidence": float(food.confidence_score) if food.confidence_score else 0.0,
                        "food_class": food.food_class,
                        "bounding_box": food.bounding_box
                    }
                    for food in meal.detected_foods
                ],
                "feedback": {
                    "feedback_text": feedback.feedback_text if feedback else None,
                    "recommendations": feedback.recommendations if feedback else None,
                    "feedback_date": feedback.feedback_date.isoformat() if feedback else None
                } if feedback else None
            }
            meal_data.append(meal_info)

        has_more = (request.offset + len(meals)) < total_count

        return MealHistoryResponse(
            meals=meal_data,
            total_count=total_count,
            has_more=has_more,
            limit=request.limit,
            offset=request.offset
        )

    async def delete_meal_history(
        self,
        student_id: UUID,
        db: Session,
        meal_ids: Optional[List[UUID]] = None,
        before_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Delete meal history with privacy compliance."""

        # Base query for student's meals
        query = db.query(Meal).filter(Meal.student_id == student_id)

        # Apply filters
        if meal_ids:
            query = query.filter(Meal.id.in_(meal_ids))
        elif before_date:
            query = query.filter(Meal.upload_date < before_date)
        else:
            # Delete all history if no specific filters
            pass

        meals_to_delete = query.all()
        deleted_count = len(meals_to_delete)

        if deleted_count == 0:
            return {
                "deleted_meals": 0,
                "deleted_feedback": 0,
                "deleted_detected_foods": 0,
                "message": "No meals found matching criteria"
            }

        # Count related records before deletion
        meal_ids_to_delete = [meal.id for meal in meals_to_delete]

        feedback_count = db.query(FeedbackRecord).filter(
            FeedbackRecord.meal_id.in_(meal_ids_to_delete)
        ).count()

        detected_foods_count = db.query(DetectedFood).filter(
            DetectedFood.meal_id.in_(meal_ids_to_delete)
        ).count()

        # Delete in correct order (foreign key constraints)
        # 1. Delete feedback records
        db.query(FeedbackRecord).filter(
            FeedbackRecord.meal_id.in_(meal_ids_to_delete)
        ).delete(synchronize_session=False)

        # 2. Delete detected foods
        db.query(DetectedFood).filter(
            DetectedFood.meal_id.in_(meal_ids_to_delete)
        ).delete(synchronize_session=False)

        # 3. Delete meals
        db.query(Meal).filter(
            Meal.id.in_(meal_ids_to_delete)
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Deleted {deleted_count} meals for student {student_id}")

        return {
            "deleted_meals": deleted_count,
            "deleted_feedback": feedback_count,
            "deleted_detected_foods": detected_foods_count,
            "message": f"Successfully deleted {deleted_count} meals and related data"
        }

    async def get_nutrition_trends(
        self,
        student_id: UUID,
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get nutrition trends for a student over specified period."""

        # Check if student has history enabled
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.history_enabled:
            return {
                "error": "History not enabled for this student",
                "trends": None
            }

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get meals with detected foods and feedback
        meals = db.query(Meal).filter(
            and_(
                Meal.student_id == student_id,
                Meal.upload_date >= cutoff_date
            )
        ).options(
            joinedload(Meal.detected_foods),
            joinedload(Meal.feedback_records)
        ).order_by(Meal.upload_date).all()

        if not meals:
            return {
                "total_meals": 0,
                "period_days": days,
                "nutrition_frequency": {},
                "balance_trend": "no_data",
                "recommendations_count": 0
            }

        # Analyze nutrition patterns
        food_class_counts = {}
        balance_scores = []
        total_recommendations = 0

        for meal in meals:
            # Count food classes
            for food in meal.detected_foods:
                food_class = food.food_class
                food_class_counts[food_class] = food_class_counts.get(
                    food_class, 0) + 1

            # Extract balance scores from feedback
            if meal.feedback_records:
                latest_feedback = max(
                    meal.feedback_records, key=lambda f: f.feedback_date)
                if latest_feedback.recommendations:
                    recommendations_data = latest_feedback.recommendations
                    if isinstance(recommendations_data, dict):
                        balance_score = recommendations_data.get(
                            "balance_score", 0.0)
                        balance_scores.append(balance_score)

                        suggestions = recommendations_data.get(
                            "suggestions", [])
                        total_recommendations += len(suggestions)

        # Calculate nutrition frequency
        total_meals = len(meals)
        nutrition_frequency = {
            food_class: count / total_meals
            for food_class, count in food_class_counts.items()
        }

        # Determine balance trend
        balance_trend = "stable"
        if len(balance_scores) >= 4:
            mid_point = len(balance_scores) // 2
            first_half_avg = sum(balance_scores[:mid_point]) / mid_point
            second_half_avg = sum(
                balance_scores[mid_point:]) / (len(balance_scores) - mid_point)

            if second_half_avg > first_half_avg + 0.1:
                balance_trend = "improving"
            elif second_half_avg < first_half_avg - 0.1:
                balance_trend = "declining"

        return {
            "total_meals": total_meals,
            "period_days": days,
            "nutrition_frequency": nutrition_frequency,
            "balance_trend": balance_trend,
            "average_balance_score": sum(balance_scores) / len(balance_scores) if balance_scores else 0.0,
            "recommendations_count": total_recommendations
        }

    async def update_history_consent(
        self,
        student_id: UUID,
        db: Session,
        history_enabled: bool
    ) -> Dict[str, Any]:
        """Update student's history consent and handle data accordingly."""

        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}

        old_consent = student.history_enabled
        student.history_enabled = history_enabled

        # If disabling history, optionally delete existing data
        if old_consent and not history_enabled:
            # For now, we keep the data but mark consent as disabled
            # In a production system, you might want to delete or anonymize data
            logger.info(f"Student {student_id} disabled history tracking")
        elif not old_consent and history_enabled:
            logger.info(f"Student {student_id} enabled history tracking")

        db.commit()
        db.refresh(student)

        return {
            "student_id": str(student_id),
            "history_enabled": history_enabled,
            "previous_consent": old_consent,
            "message": f"History consent updated to {history_enabled}"
        }

    async def get_meal_statistics(
        self,
        student_id: UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Get basic meal statistics for a student."""

        # Check consent
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.history_enabled:
            return {"error": "History not enabled"}

        # Get basic counts
        total_meals = db.query(Meal).filter(
            Meal.student_id == student_id).count()

        # Get meals from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_meals = db.query(Meal).filter(
            and_(
                Meal.student_id == student_id,
                Meal.upload_date >= week_ago
            )
        ).count()

        # Get meals from last 30 days
        month_ago = datetime.utcnow() - timedelta(days=30)
        monthly_meals = db.query(Meal).filter(
            and_(
                Meal.student_id == student_id,
                Meal.upload_date >= month_ago
            )
        ).count()

        # Get first meal date
        first_meal = db.query(Meal).filter(
            Meal.student_id == student_id
        ).order_by(Meal.upload_date).first()

        return {
            "total_meals": total_meals,
            "meals_last_7_days": recent_meals,
            "meals_last_30_days": monthly_meals,
            "first_meal_date": first_meal.upload_date.isoformat() if first_meal else None,
            "tracking_since": student.registration_date.isoformat()
        }


# Create service instance
history_service = HistoryService()
