"""Weekly insights generation service for nutrition analysis."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, extract
import logging

from app.models.meal import Meal, DetectedFood
from app.models.feedback import FeedbackRecord
from app.models.user import Student
from app.models.history import (
    WeeklyInsight,
    WeeklyInsightResponse,
    InsightGenerationRequest,
    NutritionSummary
)

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for generating weekly nutrition insights and trends."""

    def __init__(self):
        # Nigerian food groups and their nutritional significance
        self.food_group_weights = {
            "carbohydrates": 0.25,  # Energy foods
            "proteins": 0.25,       # Body building foods
            "fats": 0.15,          # Energy and vitamin absorption
            "vitamins": 0.20,      # Disease prevention
            "minerals": 0.15       # Body regulation
        }

        # Minimum frequency thresholds for balanced nutrition
        self.balance_thresholds = {
            "carbohydrates": 0.6,   # Should appear in 60% of meals
            "proteins": 0.5,        # Should appear in 50% of meals
            "fats": 0.3,           # Should appear in 30% of meals
            # Should appear in 70% of meals (fruits/vegetables)
            "vitamins": 0.7,
            "minerals": 0.6        # Should appear in 60% of meals
        }

    async def generate_weekly_insight(
        self,
        student_id: UUID,
        week_start_date: date,
        week_end_date: date,
        db: Session
    ) -> Optional[WeeklyInsightResponse]:
        """Generate comprehensive weekly nutrition insight."""

        # Check if student has history enabled
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.history_enabled:
            return None

        # Get meals for the week
        week_meals = await self._get_week_meals(student_id, week_start_date, week_end_date, db)

        if not week_meals:
            return WeeklyInsightResponse(
                student_id=student_id,
                week_period=f"{week_start_date} to {week_end_date}",
                meals_analyzed=0,
                nutrition_balance={},
                improvement_areas=[],
                positive_trends=[],
                recommendations="No meals recorded this week. Try to log your meals regularly for better insights!",
                generated_at=datetime.utcnow()
            )

        # Analyze nutrition patterns
        nutrition_analysis = await self._analyze_nutrition_patterns(week_meals)

        # Generate insights and recommendations
        insights = await self._generate_insights(nutrition_analysis, len(week_meals))

        # Store insight in database
        weekly_insight = WeeklyInsight(
            student_id=student_id,
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            nutrition_summary=nutrition_analysis,
            recommendations=insights["recommendations"]
        )

        db.add(weekly_insight)
        db.commit()
        db.refresh(weekly_insight)

        return WeeklyInsightResponse(
            student_id=student_id,
            week_period=f"{week_start_date} to {week_end_date}",
            meals_analyzed=len(week_meals),
            nutrition_balance=nutrition_analysis["food_group_frequencies"],
            improvement_areas=insights["improvement_areas"],
            positive_trends=insights["positive_trends"],
            recommendations=insights["recommendations"],
            generated_at=weekly_insight.generated_at
        )

    async def get_weekly_insight(
        self,
        student_id: UUID,
        week_start_date: date,
        db: Session
    ) -> Optional[WeeklyInsightResponse]:
        """Get existing weekly insight or generate new one."""

        # Calculate week end date
        week_end_date = week_start_date + timedelta(days=6)

        # Check for existing insight
        existing_insight = db.query(WeeklyInsight).filter(
            and_(
                WeeklyInsight.student_id == student_id,
                WeeklyInsight.week_start_date == week_start_date,
                WeeklyInsight.week_end_date == week_end_date
            )
        ).first()

        if existing_insight:
            return WeeklyInsightResponse(
                student_id=student_id,
                week_period=f"{week_start_date} to {week_end_date}",
                meals_analyzed=existing_insight.nutrition_summary.get(
                    "total_meals", 0),
                nutrition_balance=existing_insight.nutrition_summary.get(
                    "food_group_frequencies", {}),
                improvement_areas=existing_insight.nutrition_summary.get(
                    "improvement_areas", []),
                positive_trends=existing_insight.nutrition_summary.get(
                    "positive_trends", []),
                recommendations=existing_insight.recommendations,
                generated_at=existing_insight.generated_at
            )

        # Generate new insight if none exists
        return await self.generate_weekly_insight(student_id, week_start_date, week_end_date, db)

    async def get_trend_analysis(
        self,
        student_id: UUID,
        weeks: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze nutrition trends over multiple weeks."""

        # Check consent
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.history_enabled:
            return {"error": "History not enabled"}

        # Get weekly insights for the specified period
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks)

        weekly_insights = db.query(WeeklyInsight).filter(
            and_(
                WeeklyInsight.student_id == student_id,
                WeeklyInsight.week_start_date >= start_date,
                WeeklyInsight.week_end_date <= end_date
            )
        ).order_by(WeeklyInsight.week_start_date).all()

        if not weekly_insights:
            return {
                "weeks_analyzed": 0,
                "trend_direction": "no_data",
                "consistency_score": 0.0,
                "recommendations": ["Start logging meals regularly to track your nutrition trends!"]
            }

        # Analyze trends
        balance_scores = []
        meal_counts = []

        for insight in weekly_insights:
            nutrition_summary = insight.nutrition_summary or {}
            balance_score = nutrition_summary.get("overall_balance_score", 0.0)
            meal_count = nutrition_summary.get("total_meals", 0)

            balance_scores.append(balance_score)
            meal_counts.append(meal_count)

        # Calculate trend direction
        trend_direction = self._calculate_trend_direction(balance_scores)

        # Calculate consistency (how regularly meals are logged)
        avg_meals_per_week = sum(meal_counts) / \
            len(meal_counts) if meal_counts else 0
        # Assuming 2 meals per day as target
        consistency_score = min(avg_meals_per_week / 14, 1.0)

        # Generate trend-based recommendations
        trend_recommendations = self._generate_trend_recommendations(
            trend_direction, consistency_score, balance_scores
        )

        return {
            "weeks_analyzed": len(weekly_insights),
            "trend_direction": trend_direction,
            "consistency_score": consistency_score,
            "average_balance_score": sum(balance_scores) / len(balance_scores) if balance_scores else 0.0,
            "recommendations": trend_recommendations
        }

    async def _get_week_meals(
        self,
        student_id: UUID,
        week_start: date,
        week_end: date,
        db: Session
    ) -> List[Meal]:
        """Get all meals for a specific week."""

        start_datetime = datetime.combine(week_start, datetime.min.time())
        end_datetime = datetime.combine(week_end, datetime.max.time())

        return db.query(Meal).filter(
            and_(
                Meal.student_id == student_id,
                Meal.upload_date >= start_datetime,
                Meal.upload_date <= end_datetime
            )
        ).options(
            joinedload(Meal.detected_foods),
            joinedload(Meal.feedback_records)
        ).order_by(Meal.upload_date).all()

    async def _analyze_nutrition_patterns(self, meals: List[Meal]) -> Dict[str, Any]:
        """Analyze nutrition patterns from meals."""

        food_group_counts = {}
        total_meals = len(meals)
        balance_scores = []
        daily_patterns = {}

        for meal in meals:
            meal_date = meal.upload_date.date()

            # Count food groups in this meal
            meal_food_groups = set()
            for food in meal.detected_foods:
                food_class = food.food_class
                food_group_counts[food_class] = food_group_counts.get(
                    food_class, 0) + 1
                meal_food_groups.add(food_class)

            # Track daily patterns
            if meal_date not in daily_patterns:
                daily_patterns[meal_date] = set()
            daily_patterns[meal_date].update(meal_food_groups)

            # Extract balance score from feedback
            if meal.feedback_records:
                latest_feedback = max(
                    meal.feedback_records, key=lambda f: f.feedback_date)
                if latest_feedback.recommendations:
                    recommendations_data = latest_feedback.recommendations
                    if isinstance(recommendations_data, dict):
                        balance_score = recommendations_data.get(
                            "balance_score", 0.0)
                        balance_scores.append(balance_score)

        # Calculate frequencies
        food_group_frequencies = {
            food_group: count / total_meals
            for food_group, count in food_group_counts.items()
        }

        # Calculate overall balance score
        overall_balance_score = sum(
            balance_scores) / len(balance_scores) if balance_scores else 0.0

        # Analyze daily variety
        daily_variety_scores = []
        for day_groups in daily_patterns.values():
            variety_score = len(day_groups) / 5.0  # 5 main food groups
            daily_variety_scores.append(min(variety_score, 1.0))

        avg_daily_variety = sum(
            daily_variety_scores) / len(daily_variety_scores) if daily_variety_scores else 0.0

        return {
            "total_meals": total_meals,
            "food_group_frequencies": food_group_frequencies,
            "overall_balance_score": overall_balance_score,
            "average_daily_variety": avg_daily_variety,
            "days_with_meals": len(daily_patterns),
            "balance_scores": balance_scores
        }

    async def _generate_insights(self, nutrition_analysis: Dict[str, Any], total_meals: int) -> Dict[str, Any]:
        """Generate insights and recommendations from nutrition analysis."""

        food_frequencies = nutrition_analysis["food_group_frequencies"]
        balance_score = nutrition_analysis["overall_balance_score"]
        daily_variety = nutrition_analysis["average_daily_variety"]

        improvement_areas = []
        positive_trends = []
        recommendations = []

        # Analyze each food group
        for food_group, threshold in self.balance_thresholds.items():
            frequency = food_frequencies.get(food_group, 0.0)

            if frequency < threshold:
                improvement_areas.append(f"Increase {food_group} intake")
                recommendations.extend(
                    self._get_food_group_recommendations(food_group))
            elif frequency >= threshold * 1.2:  # 20% above threshold
                positive_trends.append(f"Good {food_group} intake")

        # Overall balance assessment
        if balance_score >= 0.8:
            positive_trends.append("Excellent overall meal balance")
            recommendations.append(
                "Keep up the great work with your balanced meals!")
        elif balance_score >= 0.6:
            positive_trends.append("Good meal balance")
            recommendations.append(
                "You're doing well! Try to maintain this balance consistently.")
        else:
            improvement_areas.append("Overall meal balance needs improvement")
            recommendations.append(
                "Focus on including foods from all major food groups in your meals.")

        # Daily variety assessment
        if daily_variety >= 0.8:
            positive_trends.append("Great daily food variety")
        elif daily_variety < 0.5:
            improvement_areas.append("Limited daily food variety")
            recommendations.append(
                "Try to include different types of foods each day for better nutrition.")

        # Meal frequency assessment
        if total_meals < 7:  # Less than 1 meal per day on average
            improvement_areas.append("Inconsistent meal logging")
            recommendations.append(
                "Try to log your meals more regularly to get better insights.")

        # Generate final recommendation text
        recommendation_text = self._format_recommendations(
            recommendations, positive_trends, improvement_areas)

        return {
            "improvement_areas": improvement_areas,
            "positive_trends": positive_trends,
            "recommendations": recommendation_text
        }

    def _get_food_group_recommendations(self, food_group: str) -> List[str]:
        """Get specific recommendations for each food group."""

        recommendations = {
            "carbohydrates": [
                "Include more energy foods like rice, yam, plantain, or bread in your meals.",
                "Try traditional Nigerian staples like amala, fufu, or eba for sustained energy."
            ],
            "proteins": [
                "Add more protein sources like beans, fish, chicken, or eggs to your meals.",
                "Consider Nigerian protein-rich foods like moimoi, akara, or suya."
            ],
            "fats": [
                "Include healthy fats from palm oil, groundnuts, or avocado in moderation.",
                "Use small amounts of oil when cooking vegetables or proteins."
            ],
            "vitamins": [
                "Eat more fruits like oranges, bananas, mangoes, or pawpaw daily.",
                "Include colorful vegetables in your meals for essential vitamins."
            ],
            "minerals": [
                "Add more leafy vegetables like ugwu, waterleaf, or spinach to your diet.",
                "Include mineral-rich foods like beans, fish, and green vegetables."
            ]
        }

        return recommendations.get(food_group, ["Include more variety in this food group."])

    def _calculate_trend_direction(self, balance_scores: List[float]) -> str:
        """Calculate the overall trend direction from balance scores."""

        if len(balance_scores) < 2:
            return "insufficient_data"

        # Compare first half vs second half
        mid_point = len(balance_scores) // 2
        first_half_avg = sum(balance_scores[:mid_point]) / mid_point
        second_half_avg = sum(
            balance_scores[mid_point:]) / (len(balance_scores) - mid_point)

        difference = second_half_avg - first_half_avg

        if difference > 0.1:
            return "improving"
        elif difference < -0.1:
            return "declining"
        else:
            return "stable"

    def _generate_trend_recommendations(
        self,
        trend_direction: str,
        consistency_score: float,
        balance_scores: List[float]
    ) -> List[str]:
        """Generate recommendations based on trends."""

        recommendations = []

        if trend_direction == "improving":
            recommendations.append(
                "Great job! Your nutrition balance is improving over time.")
            recommendations.append(
                "Keep following the patterns that are working for you.")
        elif trend_direction == "declining":
            recommendations.append(
                "Your nutrition balance has been declining recently.")
            recommendations.append(
                "Review your recent meals and try to include more variety.")
        elif trend_direction == "stable":
            avg_score = sum(balance_scores) / \
                len(balance_scores) if balance_scores else 0.0
            if avg_score >= 0.7:
                recommendations.append(
                    "You're maintaining good nutrition balance consistently.")
            else:
                recommendations.append(
                    "Your nutrition balance is stable but could be improved.")

        if consistency_score < 0.5:
            recommendations.append(
                "Try to log your meals more regularly for better tracking.")
        elif consistency_score >= 0.8:
            recommendations.append("Excellent meal logging consistency!")

        return recommendations

    def _format_recommendations(
        self,
        recommendations: List[str],
        positive_trends: List[str],
        improvement_areas: List[str]
    ) -> str:
        """Format recommendations into a cohesive message."""

        message_parts = []

        if positive_trends:
            message_parts.append("What you're doing well: " +
                                 ", ".join(positive_trends[:2]) + ".")

        if improvement_areas:
            message_parts.append("Areas to focus on: " +
                                 ", ".join(improvement_areas[:2]) + ".")

        if recommendations:
            message_parts.append("Recommendations: " +
                                 " ".join(recommendations[:3]))

        return " ".join(message_parts)


# Create service instance
insights_service = InsightsService()
