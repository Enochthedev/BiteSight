"""Dataset management endpoints for Nigerian foods."""

import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.admin_dependencies import (
    require_dataset_management, require_dataset_manager_or_admin
)
from app.models.admin import AdminUser
from app.models.meal import (
    NigerianFood, NigerianFoodCreate, NigerianFoodUpdate, NigerianFoodResponse,
    NigerianFoodBulkCreate, NigerianFoodBulkResponse, NigerianFoodSearchRequest,
    NigerianFoodSearchResponse
)
from app.services.nigerian_food_service import NigerianFoodService

router = APIRouter()


@router.post("/foods", response_model=NigerianFoodResponse, status_code=status.HTTP_201_CREATED)
async def create_food_item(
    food_data: NigerianFoodCreate,
    current_admin: AdminUser = Depends(require_dataset_management),
    db: Session = Depends(get_db)
):
    """Create a new Nigerian food item."""
    food_service = NigerianFoodService(db)

    try:
        food_item = food_service.create_food_item(food_data)
        return NigerianFoodResponse(
            id=food_item.id,
            food_name=food_item.food_name,
            local_names=food_item.local_names,
            food_class=food_item.food_class,
            nutritional_info=food_item.nutritional_info,
            cultural_context=food_item.cultural_context,
            created_at=food_item.created_at,
            updated_at=food_item.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create food item"
        )


@router.get("/foods/search", response_model=NigerianFoodSearchResponse)
async def search_food_items(
    query: Optional[str] = Query(
        None, description="Search term for food name or local names"),
    food_class: Optional[str] = Query(
        None, description="Filter by food class"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of records to return"),
    current_admin: AdminUser = Depends(require_dataset_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Search Nigerian food items with filters."""
    food_service = NigerianFoodService(db)

    search_request = NigerianFoodSearchRequest(
        query=query,
        food_class=food_class,
        skip=skip,
        limit=limit
    )

    foods, total_count = food_service.search_food_items(search_request)

    return NigerianFoodSearchResponse(
        foods=[
            NigerianFoodResponse(
                id=food.id,
                food_name=food.food_name,
                local_names=food.local_names,
                food_class=food.food_class,
                nutritional_info=food.nutritional_info,
                cultural_context=food.cultural_context,
                created_at=food.created_at,
                updated_at=food.updated_at
            )
            for food in foods
        ],
        total_count=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/foods/{food_id}", response_model=NigerianFoodResponse)
async def get_food_item(
    food_id: UUID,
    current_admin: AdminUser = Depends(require_dataset_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Get Nigerian food item by ID."""
    food_service = NigerianFoodService(db)

    food_item = food_service.get_food_item(food_id)
    if not food_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )

    return NigerianFoodResponse(
        id=food_item.id,
        food_name=food_item.food_name,
        local_names=food_item.local_names,
        food_class=food_item.food_class,
        nutritional_info=food_item.nutritional_info,
        cultural_context=food_item.cultural_context,
        created_at=food_item.created_at,
        updated_at=food_item.updated_at
    )


@router.put("/foods/{food_id}", response_model=NigerianFoodResponse)
async def update_food_item(
    food_id: UUID,
    food_data: NigerianFoodUpdate,
    current_admin: AdminUser = Depends(require_dataset_management),
    db: Session = Depends(get_db)
):
    """Update Nigerian food item."""
    food_service = NigerianFoodService(db)

    try:
        updated_food = food_service.update_food_item(food_id, food_data)
        if not updated_food:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Food item not found"
            )

        return NigerianFoodResponse(
            id=updated_food.id,
            food_name=updated_food.food_name,
            local_names=updated_food.local_names,
            food_class=updated_food.food_class,
            nutritional_info=updated_food.nutritional_info,
            cultural_context=updated_food.cultural_context,
            created_at=updated_food.created_at,
            updated_at=updated_food.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update food item"
        )


@router.delete("/foods/{food_id}")
async def delete_food_item(
    food_id: UUID,
    current_admin: AdminUser = Depends(require_dataset_management),
    db: Session = Depends(get_db)
):
    """Delete Nigerian food item."""
    food_service = NigerianFoodService(db)

    success = food_service.delete_food_item(food_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )

    return {"message": "Food item successfully deleted"}


@router.post("/foods/bulk", response_model=NigerianFoodBulkResponse)
async def bulk_create_food_items(
    bulk_data: NigerianFoodBulkCreate,
    current_admin: AdminUser = Depends(require_dataset_management),
    db: Session = Depends(get_db)
):
    """Bulk create Nigerian food items."""
    food_service = NigerianFoodService(db)

    try:
        result = food_service.bulk_create_food_items(bulk_data)

        return NigerianFoodBulkResponse(
            created_count=result["created_count"],
            failed_count=result["failed_count"],
            created_foods=[
                NigerianFoodResponse(
                    id=food.id,
                    food_name=food.food_name,
                    local_names=food.local_names,
                    food_class=food.food_class,
                    nutritional_info=food.nutritional_info,
                    cultural_context=food.cultural_context,
                    created_at=food.created_at,
                    updated_at=food.updated_at
                )
                for food in result["created_foods"]
            ],
            errors=result["errors"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create food items"
        )


@router.post("/foods/import", response_model=NigerianFoodBulkResponse)
async def import_foods_from_json(
    file: UploadFile = File(...,
                            description="JSON file containing food items"),
    current_admin: AdminUser = Depends(require_dataset_management),
    db: Session = Depends(get_db)
):
    """Import Nigerian foods from JSON file."""
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file"
        )

    # Read file content
    try:
        content = await file.read()
        file_content = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file content"
        )

    food_service = NigerianFoodService(db)

    try:
        result = food_service.import_from_json(file_content)

        return NigerianFoodBulkResponse(
            created_count=result["created_count"],
            failed_count=result["failed_count"],
            created_foods=[
                NigerianFoodResponse(
                    id=food.id,
                    food_name=food.food_name,
                    local_names=food.local_names,
                    food_class=food.food_class,
                    nutritional_info=food.nutritional_info,
                    cultural_context=food.cultural_context,
                    created_at=food.created_at,
                    updated_at=food.updated_at
                )
                for food in result["created_foods"]
            ],
            errors=result["errors"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import food items"
        )


@router.get("/foods/export")
async def export_foods_to_json(
    food_class: Optional[str] = Query(
        None, description="Filter by food class"),
    current_admin: AdminUser = Depends(require_dataset_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Export Nigerian foods to JSON format."""
    food_service = NigerianFoodService(db)

    try:
        foods_data = food_service.export_to_json(food_class=food_class)

        filename = f"nigerian_foods_{food_class or 'all'}.json"

        return JSONResponse(
            content=foods_data,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export food items"
        )


@router.get("/foods/classes")
async def get_food_classes(
    current_admin: AdminUser = Depends(require_dataset_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Get all unique food classes."""
    food_service = NigerianFoodService(db)

    try:
        classes = food_service.get_food_classes()
        return {"food_classes": classes}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve food classes"
        )


@router.get("/statistics")
async def get_dataset_statistics(
    current_admin: AdminUser = Depends(require_dataset_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Get dataset statistics."""
    food_service = NigerianFoodService(db)

    try:
        stats = food_service.get_dataset_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dataset statistics"
        )


@router.post("/foods/validate")
async def validate_food_data(
    food_data: dict,
    current_admin: AdminUser = Depends(require_dataset_manager_or_admin),
    db: Session = Depends(get_db)
):
    """Validate food data format."""
    food_service = NigerianFoodService(db)

    try:
        errors = food_service.validate_food_data(food_data)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate food data"
        )
