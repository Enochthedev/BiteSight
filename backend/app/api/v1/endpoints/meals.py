"""Meal management endpoints."""

from uuid import UUID, uuid4
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse

from app.services.image_service import image_service
from app.services.image_metadata_service import get_image_metadata_service
from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import Student
from app.models.image_metadata import ImageSearchQuery, ImageSearchResponse, ImageMetadataResponse
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_meal_image(
    file: UploadFile = File(...),
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload meal image for analysis."""
    try:
        # Generate unique meal ID
        meal_id = uuid4()

        # Save image with validation, preprocessing, and metadata
        result = await image_service.save_image(
            file, meal_id, current_user.id, db
        )

        return {
            "success": True,
            "meal_id": result["meal_id"],
            "message": "Image uploaded successfully",
            "validation_results": result["validation_results"],
            "file_info": {
                "file_size": result["file_size"],
                "file_hash": result["file_hash"],
                "has_processed": result["processed_path"] is not None,
                "has_thumbnail": result["thumbnail_path"] is not None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading image: {str(e)}"
        )


@router.get("/{meal_id}/image")
async def get_meal_image(
    meal_id: UUID,
    image_type: str = "processed",  # raw, processed, or thumbnail
    current_user: Student = Depends(get_current_user)
):
    """Get meal image by type."""
    try:
        paths = image_service.get_image_paths(meal_id)

        if image_type not in paths or not paths[image_type]:
            raise HTTPException(
                status_code=404,
                detail=f"Image type '{image_type}' not found for meal {meal_id}"
            )

        image_path = paths[image_type]
        return FileResponse(
            image_path,
            media_type="image/jpeg",
            filename=f"{meal_id}_{image_type}.jpg"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )


@router.get("/{meal_id}/metadata")
async def get_meal_metadata(
    meal_id: UUID,
    current_user: Student = Depends(get_current_user)
):
    """Get meal image metadata."""
    try:
        paths = image_service.get_image_paths(meal_id)

        if not paths.get("raw"):
            raise HTTPException(
                status_code=404,
                detail=f"Meal {meal_id} not found"
            )

        metadata = image_service.get_image_metadata(paths["raw"])

        return {
            "meal_id": str(meal_id),
            "available_images": {k: v is not None for k, v in paths.items()},
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metadata: {str(e)}"
        )


@router.delete("/{meal_id}")
async def delete_meal_images(
    meal_id: UUID,
    current_user: Student = Depends(get_current_user)
):
    """Delete all images for a meal."""
    try:
        results = image_service.delete_meal_images(meal_id)

        return {
            "success": True,
            "meal_id": str(meal_id),
            "deleted_images": results,
            "message": "Meal images deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting meal images: {str(e)}"
        )


@router.get("/{meal_id}/analysis")
async def get_meal_analysis():
    """Get meal analysis results."""
    return {"message": "Meal analysis endpoint - to be implemented"}


@router.get("/search")
async def search_images(
    student_id: UUID = None,
    date_from: datetime = None,
    date_to: datetime = None,
    min_quality_score: int = None,
    has_processing_errors: bool = None,
    image_format: str = None,
    min_resolution: int = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search images with filtering and pagination."""
    try:
        # If not admin, restrict to current user's images
        search_student_id = student_id if student_id else current_user.id

        query = ImageSearchQuery(
            student_id=search_student_id,
            date_from=date_from,
            date_to=date_to,
            min_quality_score=min_quality_score,
            has_processing_errors=has_processing_errors,
            image_format=image_format,
            min_resolution=min_resolution,
            limit=limit,
            offset=offset
        )

        metadata_service = get_image_metadata_service(db)
        results, total_count = metadata_service.search_images(query)

        return ImageSearchResponse(
            images=[ImageMetadataResponse.from_orm(img) for img in results],
            total_count=total_count,
            has_more=(offset + limit) < total_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching images: {str(e)}"
        )


@router.get("/stats")
async def get_image_stats(
    current_user: Student = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get image statistics for current user."""
    try:
        metadata_service = get_image_metadata_service(db)
        stats = metadata_service.get_student_image_stats(current_user.id)

        return {
            "success": True,
            "student_id": str(current_user.id),
            "statistics": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting image statistics: {str(e)}"
        )


@router.get("/{meal_id}")
async def get_meal():
    """Get meal details."""
    return {"message": "Get meal endpoint - to be implemented"}
