"""Admin endpoints for dataset and rule management."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/foods")
async def create_nigerian_food():
    """Add new Nigerian food to dataset."""
    return {"message": "Create food endpoint - to be implemented"}


@router.get("/foods")
async def list_nigerian_foods():
    """List Nigerian foods in dataset."""
    return {"message": "List foods endpoint - to be implemented"}


@router.post("/rules")
async def create_nutrition_rule():
    """Create new nutrition rule."""
    return {"message": "Create rule endpoint - to be implemented"}


@router.get("/rules")
async def list_nutrition_rules():
    """List nutrition rules."""
    return {"message": "List rules endpoint - to be implemented"}