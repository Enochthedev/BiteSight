"""Meal history and insights endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.history import MealHistoryRequest, MealHistoryResponse, WeeklyInsightResponse
from app.models.user import Student
from app.services.history_service import history_service
from app.services.insights_service import insights_service

router = APIRouter()


@router.get("/meals", response_model=MealHistoryResponse)
async def get_meal_history(
    start_date: Optional[date] = Query(
        None, description="Start date for filtering meals"),
    end_date: Optional[date] = Query(
        None, description="End date for filtering meals"),
    limit: int = Query(
        50, ge=1, le=100, description="Number of meals to return"),
    offset: int = Query(0, ge=0, description="Number of meals to skip"),
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get student's meal history with filtering and pagination."""

    request = MealHistoryRequest(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    try:
        history = await history_service.get_meal_history(
            student_id=current_student.id,
            db=db,
            request=request
        )
        return history
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving meal history: {str(e)}")


@router.get("/statistics")
async def get_meal_statistics(
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get basic meal statistics for the current student."""

    try:
        stats = await history_service.get_meal_statistics(
            student_id=current_student.id,
            db=db
        )

        if "error" in stats:
            raise HTTPException(status_code=403, detail=stats["error"])

        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.get("/trends")
async def get_nutrition_trends(
    days: int = Query(30, ge=1, le=365,
                      description="Number of days to analyze"),
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get nutrition trends for the specified period."""

    try:
        trends = await history_service.get_nutrition_trends(
            student_id=current_student.id,
            db=db,
            days=days
        )

        if "error" in trends:
            raise HTTPException(status_code=403, detail=trends["error"])

        return trends
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving trends: {str(e)}")


@router.delete("/meals")
async def delete_meal_history(
    meal_ids: Optional[List[UUID]] = Query(
        None, description="Specific meal IDs to delete"),
    before_date: Optional[date] = Query(
        None, description="Delete meals before this date"),
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete student's meal history with privacy compliance."""

    # Validate that at least one deletion criteria is provided
    if not meal_ids and not before_date:
        raise HTTPException(
            status_code=400,
            detail="Must specify either meal_ids or before_date for deletion"
        )

    try:
        result = await history_service.delete_meal_history(
            student_id=current_student.id,
            db=db,
            meal_ids=meal_ids,
            before_date=before_date
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting meal history: {str(e)}")


@router.put("/consent")
async def update_history_consent(
    history_enabled: bool,
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update student's consent for meal history storage."""

    try:
        result = await history_service.update_history_consent(
            student_id=current_student.id,
            db=db,
            history_enabled=history_enabled
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating consent: {str(e)}")


@router.get("/insights/weekly", response_model=WeeklyInsightResponse)
async def get_weekly_insights(
    week_start_date: date = Query(...,
                                  description="Start date of the week (YYYY-MM-DD)"),
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get weekly nutrition insights for a specific week."""

    try:
        insight = await insights_service.get_weekly_insight(
            student_id=current_student.id,
            week_start_date=week_start_date,
            db=db
        )

        if not insight:
            raise HTTPException(
                status_code=403,
                detail="History not enabled or no data available for this week"
            )

        return insight
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating weekly insights: {str(e)}")


@router.post("/insights/weekly/generate", response_model=WeeklyInsightResponse)
async def generate_weekly_insights(
    week_start_date: date,
    week_end_date: date,
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate new weekly insights for a specific week period."""

    # Validate date range
    if week_end_date <= week_start_date:
        raise HTTPException(
            status_code=400, detail="End date must be after start date")

    if (week_end_date - week_start_date).days > 7:
        raise HTTPException(
            status_code=400, detail="Week period cannot exceed 7 days")

    try:
        insight = await insights_service.generate_weekly_insight(
            student_id=current_student.id,
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            db=db
        )

        if not insight:
            raise HTTPException(
                status_code=403,
                detail="History not enabled for this student"
            )

        return insight
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating weekly insights: {str(e)}")


@router.get("/insights/trends")
async def get_nutrition_trend_analysis(
    weeks: int = Query(
        4, ge=1, le=12, description="Number of weeks to analyze"),
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get nutrition trend analysis over multiple weeks."""

    try:
        trends = await insights_service.get_trend_analysis(
            student_id=current_student.id,
            weeks=weeks,
            db=db
        )

        if "error" in trends:
            raise HTTPException(status_code=403, detail=trends["error"])

        return trends
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing trends: {str(e)}")
