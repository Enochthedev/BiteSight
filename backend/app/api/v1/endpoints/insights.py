"""Weekly insights endpoints for mobile app."""

from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.history import WeeklyInsightResponse
from app.models.user import Student
from app.services.insights_service import insights_service

router = APIRouter()


@router.get("/weekly", response_model=List[WeeklyInsightResponse])
async def get_weekly_insights(
    weeks: int = 4,
    current_student: Student = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly nutrition insights for mobile app.
    Returns recent weeks of insights without requiring week_start_date parameter.
    
    Args:
        weeks: Number of recent weeks to return (default: 4)
        current_student: Authenticated student
        db: Database session
        
    Returns:
        List of weekly insights for the specified number of recent weeks
    """
    try:
        insights = []
        today = date.today()
        
        # Generate insights for the requested number of recent weeks
        for week_offset in range(weeks):
            # Calculate week start date (going backwards from today)
            days_back = week_offset * 7
            week_start = today - timedelta(days=days_back + today.weekday())
            
            # Get or generate insight for this week
            insight = await insights_service.get_weekly_insight(
                student_id=current_student.id,
                week_start_date=week_start,
                db=db
            )
            
            if insight:
                insights.append(insight)
        
        return insights
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving weekly insights: {str(e)}"
        )
