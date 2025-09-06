"""Feedback service for nutrition analysis."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from app.models.feedback import FeedbackRecord, NutritionFeedback
from app.models.meal import FoodDetectionResult
from app.services.analysis_service import analysis_service
from app.services.feedback_generation_service import nigerian_feedback_generator, CulturalContext
from app.core.nutrition_engine import nutrition_engine, NutritionProfile
from app.core.database import get_db

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for generating and managing nutrition feedback."""

    def __init__(self):
        self.analysis_service = analysis_service
        self.feedback_generator = nigerian_feedback_generator
        self.nutrition_engine = nutrition_engine

    async def generate_feedback(self,
                                meal_id: UUID,
                                student_id: UUID,
                                detected_foods: List[FoodDetectionResult],
                                db: Session,
                                cultural_context: str = "nigerian_general") -> NutritionFeedback:
        """Generate comprehensive nutrition feedback for a meal."""

        try:
            # Convert cultural context string to enum
            context_enum = CulturalContext(cultural_context)
        except ValueError:
            context_enum = CulturalContext.NIGERIAN_GENERAL

        try:
            # Perform complete nutrition analysis using rule engine
            analysis_result = await self.analysis_service.analyze_nutrition_with_rules(detected_foods)

            # Extract nutrition profile
            nutrition_profile = NutritionProfile(
                carbohydrates=analysis_result["nutrition_profile"].get(
                    "carbohydrates", 0.0),
                proteins=analysis_result["nutrition_profile"].get(
                    "proteins", 0.0),
                fats=analysis_result["nutrition_profile"].get("fats", 0.0),
                vitamins=analysis_result["nutrition_profile"].get(
                    "vitamins", 0.0),
                minerals=analysis_result["nutrition_profile"].get(
                    "minerals", 0.0),
                water=analysis_result["nutrition_profile"].get("water", 0.0)
            )

            # Convert matching rules to NutritionRule objects for feedback generation
            matching_rules = []
            for rule_data in analysis_result.get("matching_rules", []):
                from app.core.nutrition_engine import NutritionRule
                rule = NutritionRule(
                    rule_id=rule_data["rule_id"],
                    name=rule_data["name"],
                    conditions=[],  # Not needed for feedback generation
                    feedback_template=rule_data["feedback_template"],
                    priority=rule_data["priority"]
                )
                matching_rules.append(rule)

            # Convert detected foods to dictionary format
            foods_dict = [
                {
                    "food_name": food.food_name,
                    "confidence": food.confidence,
                    "food_class": food.food_class,
                    "bounding_box": food.bounding_box
                }
                for food in detected_foods
            ]

            # Generate culturally relevant feedback
            feedback_data = self.feedback_generator.generate_feedback(
                nutrition_profile,
                foods_dict,
                matching_rules,
                context_enum
            )

            # Create comprehensive feedback message
            feedback_message = self._create_comprehensive_message(
                feedback_data)

            # Extract recommendations
            recommendations = feedback_data.get("recommendations", [])

            # Store feedback in database
            feedback_record = FeedbackRecord(
                meal_id=meal_id,
                student_id=student_id,
                feedback_text=feedback_message,
                feedback_type="comprehensive_nutrition_analysis",
                recommendations={
                    "suggestions": recommendations,
                    "specific_feedback": feedback_data.get("specific_feedback", []),
                    "cultural_context": cultural_context,
                    "balance_score": feedback_data.get("balance_score", 0.0)
                }
            )

            db.add(feedback_record)
            db.commit()
            db.refresh(feedback_record)

            # Return structured feedback
            return NutritionFeedback(
                meal_id=meal_id,
                detected_foods=[food.dict() for food in detected_foods],
                missing_food_groups=analysis_result.get(
                    "missing_food_groups", []),
                recommendations=recommendations,
                overall_balance_score=feedback_data.get("balance_score", 0.0),
                feedback_message=feedback_message
            )

        except Exception as e:
            logger.error(f"Error generating feedback for meal {meal_id}: {e}")
            # Fallback to basic feedback
            return await self._generate_basic_feedback(meal_id, student_id, detected_foods, db)

    def _create_comprehensive_message(self, feedback_data: Dict[str, Any]) -> str:
        """Create comprehensive feedback message from feedback data."""
        message_parts = []

        # Add overall message
        if feedback_data.get("overall_message"):
            message_parts.append(feedback_data["overall_message"])

        # Add specific feedback messages
        specific_feedback = feedback_data.get("specific_feedback", [])
        if specific_feedback:
            # Sort by priority and take top 2
            sorted_feedback = sorted(
                specific_feedback, key=lambda x: x.get("priority", 0), reverse=True)
            for feedback in sorted_feedback[:2]:
                message_parts.append(feedback.get("message", ""))

        # Add encouragement
        if feedback_data.get("encouragement"):
            message_parts.append(feedback_data["encouragement"])

        return " ".join(filter(None, message_parts))

    async def _generate_basic_feedback(self,
                                       meal_id: UUID,
                                       student_id: UUID,
                                       detected_foods: List[FoodDetectionResult],
                                       db: Session) -> NutritionFeedback:
        """Generate basic feedback as fallback."""

        # Use basic analysis service
        nutrition_profile = self.analysis_service.classify_nutrition(
            detected_foods)
        insights = self.analysis_service.generate_insights(nutrition_profile)

        # Generate basic recommendations
        recommendations = []
        for missing_group in insights["missing_food_groups"]:
            if missing_group == "proteins":
                recommendations.append(
                    "Add protein sources like beans, fish, or chicken")
            elif missing_group == "vitamins":
                recommendations.append(
                    "Include fruits like oranges, bananas, or mangoes")
            elif missing_group == "minerals":
                recommendations.append(
                    "Add vegetables like efo riro, ugwu, or okra soup")
            elif missing_group == "carbohydrates":
                recommendations.append(
                    "Include energy foods like rice, yam, or amala")

        # Create basic feedback message
        balance_score = insights["balance_score"]
        if balance_score > 0.8:
            feedback_message = "Excellent! Your meal is well-balanced and nutritious."
        elif balance_score > 0.6:
            feedback_message = "Good meal choice! Consider adding a bit more variety."
        elif balance_score > 0.4:
            feedback_message = "Your meal has some good elements. Try to include more food groups."
        else:
            feedback_message = "This meal could be more balanced. Consider adding variety from different food groups."

        # Store basic feedback
        feedback_record = FeedbackRecord(
            meal_id=meal_id,
            student_id=student_id,
            feedback_text=feedback_message,
            feedback_type="basic_nutrition_analysis",
            recommendations={"suggestions": recommendations}
        )

        db.add(feedback_record)
        db.commit()
        db.refresh(feedback_record)

        return NutritionFeedback(
            meal_id=meal_id,
            detected_foods=[food.dict() for food in detected_foods],
            missing_food_groups=insights["missing_food_groups"],
            recommendations=recommendations,
            overall_balance_score=balance_score,
            feedback_message=feedback_message
        )

    async def get_feedback_history(self,
                                   student_id: UUID,
                                   db: Session,
                                   limit: int = 10) -> List[FeedbackRecord]:
        """Get feedback history for a student."""
        return db.query(FeedbackRecord).filter(
            FeedbackRecord.student_id == student_id
        ).order_by(FeedbackRecord.feedback_date.desc()).limit(limit).all()

    async def get_feedback_by_meal(self,
                                   meal_id: UUID,
                                   db: Session) -> Optional[FeedbackRecord]:
        """Get feedback for a specific meal."""
        return db.query(FeedbackRecord).filter(
            FeedbackRecord.meal_id == meal_id
        ).first()

    async def update_feedback(self,
                              feedback_id: UUID,
                              updated_data: Dict[str, Any],
                              db: Session) -> Optional[FeedbackRecord]:
        """Update existing feedback record."""

        feedback_record = db.query(FeedbackRecord).filter(
            FeedbackRecord.id == feedback_id
        ).first()

        if not feedback_record:
            return None

        # Update allowed fields
        if "feedback_text" in updated_data:
            feedback_record.feedback_text = updated_data["feedback_text"]

        if "recommendations" in updated_data:
            feedback_record.recommendations = updated_data["recommendations"]

        db.commit()
        db.refresh(feedback_record)

        return feedback_record

    async def delete_feedback(self,
                              feedback_id: UUID,
                              db: Session) -> bool:
        """Delete feedback record."""

        feedback_record = db.query(FeedbackRecord).filter(
            FeedbackRecord.id == feedback_id
        ).first()

        if not feedback_record:
            return False

        db.delete(feedback_record)
        db.commit()

        return True

    async def get_student_nutrition_trends(self,
                                           student_id: UUID,
                                           db: Session,
                                           days: int = 30) -> Dict[str, Any]:
        """Get nutrition trends for a student over specified days."""

        from datetime import datetime, timedelta
        from sqlalchemy import and_

        # Get recent feedback records
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        feedback_records = db.query(FeedbackRecord).filter(
            and_(
                FeedbackRecord.student_id == student_id,
                FeedbackRecord.feedback_date >= cutoff_date
            )
        ).order_by(FeedbackRecord.feedback_date.desc()).all()

        if not feedback_records:
            return {
                "total_meals": 0,
                "average_balance_score": 0.0,
                "improvement_trend": "no_data",
                "common_missing_groups": [],
                "recommendations_given": 0
            }

        # Calculate trends
        balance_scores = []
        all_recommendations = []

        for record in feedback_records:
            recommendations_data = record.recommendations or {}

            # Extract balance score
            if isinstance(recommendations_data, dict):
                balance_score = recommendations_data.get("balance_score", 0.0)
                balance_scores.append(balance_score)

                # Extract recommendations
                suggestions = recommendations_data.get("suggestions", [])
                all_recommendations.extend(suggestions)

        # Calculate average balance score
        avg_balance_score = sum(balance_scores) / \
            len(balance_scores) if balance_scores else 0.0

        # Determine improvement trend (simple: compare first half vs second half)
        if len(balance_scores) >= 4:
            mid_point = len(balance_scores) // 2
            first_half_avg = sum(balance_scores[:mid_point]) / mid_point
            second_half_avg = sum(
                balance_scores[mid_point:]) / (len(balance_scores) - mid_point)

            if second_half_avg > first_half_avg + 0.1:
                trend = "improving"
            elif second_half_avg < first_half_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "total_meals": len(feedback_records),
            "average_balance_score": avg_balance_score,
            "improvement_trend": trend,
            "recommendations_given": len(all_recommendations),
            "period_days": days
        }


feedback_service = FeedbackService()
