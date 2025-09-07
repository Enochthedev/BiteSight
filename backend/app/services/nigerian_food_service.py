"""Nigerian food dataset management service."""

import json
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.meal import (
    NigerianFood, NigerianFoodCreate, NigerianFoodUpdate,
    NigerianFoodBulkCreate, NigerianFoodSearchRequest
)


class NigerianFoodService:
    """Service for Nigerian food dataset management."""

    def __init__(self, db: Session):
        self.db = db

    def create_food_item(self, food_data: NigerianFoodCreate) -> NigerianFood:
        """Create a new Nigerian food item."""
        # Check if food name already exists
        existing_food = self.db.query(NigerianFood).filter(
            func.lower(NigerianFood.food_name) == food_data.food_name.lower()
        ).first()

        if existing_food:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Food item '{food_data.food_name}' already exists"
            )

        # Create new food item
        food_item = NigerianFood(
            food_name=food_data.food_name,
            local_names=food_data.local_names,
            food_class=food_data.food_class,
            nutritional_info=food_data.nutritional_info,
            cultural_context=food_data.cultural_context
        )

        self.db.add(food_item)
        self.db.commit()
        self.db.refresh(food_item)

        return food_item

    def get_food_item(self, food_id: UUID) -> Optional[NigerianFood]:
        """Get Nigerian food item by ID."""
        return self.db.query(NigerianFood).filter(
            NigerianFood.id == food_id
        ).first()

    def update_food_item(self, food_id: UUID, food_data: NigerianFoodUpdate) -> Optional[NigerianFood]:
        """Update Nigerian food item."""
        food_item = self.get_food_item(food_id)
        if not food_item:
            return None

        # Check for name conflicts if updating name
        if food_data.food_name and food_data.food_name.lower() != food_item.food_name.lower():
            existing_food = self.db.query(NigerianFood).filter(
                and_(
                    func.lower(
                        NigerianFood.food_name) == food_data.food_name.lower(),
                    NigerianFood.id != food_id
                )
            ).first()

            if existing_food:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Food item '{food_data.food_name}' already exists"
                )

        # Update fields
        if food_data.food_name is not None:
            food_item.food_name = food_data.food_name
        if food_data.local_names is not None:
            food_item.local_names = food_data.local_names
        if food_data.food_class is not None:
            food_item.food_class = food_data.food_class
        if food_data.nutritional_info is not None:
            food_item.nutritional_info = food_data.nutritional_info
        if food_data.cultural_context is not None:
            food_item.cultural_context = food_data.cultural_context

        self.db.commit()
        self.db.refresh(food_item)

        return food_item

    def delete_food_item(self, food_id: UUID) -> bool:
        """Delete Nigerian food item."""
        food_item = self.get_food_item(food_id)
        if not food_item:
            return False

        self.db.delete(food_item)
        self.db.commit()
        return True

    def search_food_items(self, search_request: NigerianFoodSearchRequest) -> Tuple[List[NigerianFood], int]:
        """Search Nigerian food items with filters."""
        query = self.db.query(NigerianFood)

        # Apply search filters
        if search_request.query:
            search_term = f"%{search_request.query.lower()}%"
            query = query.filter(
                or_(
                    func.lower(NigerianFood.food_name).like(search_term),
                    func.lower(NigerianFood.cultural_context).like(
                        search_term),
                    NigerianFood.local_names.astext.ilike(search_term)
                )
            )

        if search_request.food_class:
            query = query.filter(
                func.lower(
                    NigerianFood.food_class) == search_request.food_class.lower()
            )

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        foods = query.offset(search_request.skip).limit(
            search_request.limit).all()

        return foods, total_count

    def get_food_classes(self) -> List[str]:
        """Get all unique food classes."""
        result = self.db.query(NigerianFood.food_class).distinct().all()
        return [row[0] for row in result if row[0]]

    def bulk_create_food_items(self, bulk_data: NigerianFoodBulkCreate) -> Dict[str, Any]:
        """Bulk create Nigerian food items."""
        created_foods = []
        errors = []

        for i, food_data in enumerate(bulk_data.foods):
            try:
                # Check if food already exists
                existing_food = self.db.query(NigerianFood).filter(
                    func.lower(
                        NigerianFood.food_name) == food_data.food_name.lower()
                ).first()

                if existing_food:
                    errors.append({
                        "index": i,
                        "food_name": food_data.food_name,
                        "error": f"Food item '{food_data.food_name}' already exists"
                    })
                    continue

                # Create food item
                food_item = NigerianFood(
                    food_name=food_data.food_name,
                    local_names=food_data.local_names,
                    food_class=food_data.food_class,
                    nutritional_info=food_data.nutritional_info,
                    cultural_context=food_data.cultural_context
                )

                self.db.add(food_item)
                self.db.flush()  # Get the ID without committing
                created_foods.append(food_item)

            except Exception as e:
                errors.append({
                    "index": i,
                    "food_name": food_data.food_name,
                    "error": str(e)
                })

        # Commit all successful creations
        if created_foods:
            self.db.commit()
            for food in created_foods:
                self.db.refresh(food)
        else:
            self.db.rollback()

        return {
            "created_count": len(created_foods),
            "failed_count": len(errors),
            "created_foods": created_foods,
            "errors": errors
        }

    def import_from_json(self, file_content: str) -> Dict[str, Any]:
        """Import Nigerian foods from JSON file."""
        try:
            data = json.loads(file_content)

            # Validate JSON structure
            if not isinstance(data, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON file must contain an array of food items"
                )

            # Convert to bulk create format
            foods = []
            for item in data:
                try:
                    food_create = NigerianFoodCreate(**item)
                    foods.append(food_create)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid food item format: {str(e)}"
                    )

            bulk_data = NigerianFoodBulkCreate(foods=foods)
            return self.bulk_create_food_items(bulk_data)

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )

    def export_to_json(self, food_class: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export Nigerian foods to JSON format."""
        query = self.db.query(NigerianFood)

        if food_class:
            query = query.filter(
                func.lower(NigerianFood.food_class) == food_class.lower()
            )

        foods = query.all()

        return [
            {
                "id": str(food.id),
                "food_name": food.food_name,
                "local_names": food.local_names,
                "food_class": food.food_class,
                "nutritional_info": food.nutritional_info,
                "cultural_context": food.cultural_context,
                "created_at": food.created_at.isoformat() if food.created_at else None,
                "updated_at": food.updated_at.isoformat() if food.updated_at else None
            }
            for food in foods
        ]

    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        total_foods = self.db.query(NigerianFood).count()

        # Count by food class
        class_counts = self.db.query(
            NigerianFood.food_class,
            func.count(NigerianFood.id).label('count')
        ).group_by(NigerianFood.food_class).all()

        class_distribution = {row[0]: row[1] for row in class_counts}

        # Get foods with and without nutritional info
        foods_with_nutrition = self.db.query(NigerianFood).filter(
            NigerianFood.nutritional_info.isnot(None)
        ).count()

        # Get foods with and without cultural context
        foods_with_context = self.db.query(NigerianFood).filter(
            NigerianFood.cultural_context.isnot(None)
        ).count()

        return {
            "total_foods": total_foods,
            "class_distribution": class_distribution,
            "foods_with_nutritional_info": foods_with_nutrition,
            "foods_with_cultural_context": foods_with_context,
            "completion_percentage": {
                "nutritional_info": (foods_with_nutrition / total_foods * 100) if total_foods > 0 else 0,
                "cultural_context": (foods_with_context / total_foods * 100) if total_foods > 0 else 0
            }
        }

    def validate_food_data(self, food_data: Dict[str, Any]) -> List[str]:
        """Validate food data and return list of validation errors."""
        errors = []

        # Required fields
        if not food_data.get("food_name"):
            errors.append("food_name is required")
        elif len(food_data["food_name"]) > 255:
            errors.append("food_name must be 255 characters or less")

        if not food_data.get("food_class"):
            errors.append("food_class is required")
        elif len(food_data["food_class"]) > 100:
            errors.append("food_class must be 100 characters or less")

        # Validate local_names structure if provided
        if food_data.get("local_names"):
            local_names = food_data["local_names"]
            if not isinstance(local_names, dict):
                errors.append("local_names must be a dictionary")
            else:
                for lang, names in local_names.items():
                    if not isinstance(names, list):
                        errors.append(f"local_names[{lang}] must be a list")
                    elif not all(isinstance(name, str) for name in names):
                        errors.append(
                            f"local_names[{lang}] must contain only strings")

        # Validate nutritional_info structure if provided
        if food_data.get("nutritional_info"):
            nutritional_info = food_data["nutritional_info"]
            if not isinstance(nutritional_info, dict):
                errors.append("nutritional_info must be a dictionary")

        return errors
