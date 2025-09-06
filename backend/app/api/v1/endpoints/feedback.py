"""Feedback endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{meal_id}")
async def get_meal_feedback():
    """Get nutrition feedback for a meal."""
    return {"message": "Get feedback endpoint - to be implemented"}


@router.post("/{meal_id}/generate")
async def generate_feedback():
    """Generate nutrition feedback for a meal."""
    return {"message": "Generate feedback endpoint - to be implemented"}