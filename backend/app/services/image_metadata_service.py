"""Service for managing image metadata storage and indexing."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from fastapi import HTTPException

from app.models.image_metadata import (
    ImageMetadata,
    ImageMetadataCreate,
    ImageMetadataUpdate,
    ImageSearchQuery
)
from app.core.database import get_db


class ImageMetadataService:
    """Service for image metadata operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_metadata(self, metadata: ImageMetadataCreate) -> ImageMetadata:
        """Create new image metadata record."""
        try:
            # Check if metadata already exists for this meal
            existing = self.db.query(ImageMetadata).filter(
                ImageMetadata.meal_id == metadata.meal_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image metadata already exists for meal {metadata.meal_id}"
                )

            # Create new metadata record
            db_metadata = ImageMetadata(**metadata.dict())
            self.db.add(db_metadata)
            self.db.commit()
            self.db.refresh(db_metadata)

            return db_metadata

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating image metadata: {str(e)}"
            )

    def get_metadata_by_meal_id(self, meal_id: UUID) -> Optional[ImageMetadata]:
        """Get image metadata by meal ID."""
        return self.db.query(ImageMetadata).filter(
            ImageMetadata.meal_id == meal_id
        ).first()

    def get_metadata_by_hash(self, file_hash: str) -> Optional[ImageMetadata]:
        """Get image metadata by file hash (for duplicate detection)."""
        return self.db.query(ImageMetadata).filter(
            ImageMetadata.file_hash == file_hash
        ).first()

    def update_metadata(self, meal_id: UUID, update_data: ImageMetadataUpdate) -> Optional[ImageMetadata]:
        """Update image metadata."""
        try:
            metadata = self.get_metadata_by_meal_id(meal_id)
            if not metadata:
                return None

            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(metadata, field, value)

            # Set processed_date if marking as processed
            if update_data.is_processed and not metadata.processed_date:
                metadata.processed_date = datetime.utcnow()

            self.db.commit()
            self.db.refresh(metadata)

            return metadata

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error updating image metadata: {str(e)}"
            )

    def delete_metadata(self, meal_id: UUID) -> bool:
        """Delete image metadata."""
        try:
            metadata = self.get_metadata_by_meal_id(meal_id)
            if not metadata:
                return False

            self.db.delete(metadata)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting image metadata: {str(e)}"
            )

    def search_images(self, query: ImageSearchQuery) -> tuple[List[ImageMetadata], int]:
        """Search images with filtering and pagination."""
        try:
            # Build base query
            base_query = self.db.query(ImageMetadata)

            # Apply filters
            filters = []

            if query.student_id:
                filters.append(ImageMetadata.student_id == query.student_id)

            if query.date_from:
                filters.append(ImageMetadata.upload_date >= query.date_from)

            if query.date_to:
                filters.append(ImageMetadata.upload_date <= query.date_to)

            if query.min_quality_score is not None:
                filters.append(ImageMetadata.quality_score >=
                               query.min_quality_score)

            if query.has_processing_errors is not None:
                if query.has_processing_errors:
                    filters.append(ImageMetadata.processing_error.isnot(None))
                else:
                    filters.append(ImageMetadata.processing_error.is_(None))

            if query.image_format:
                filters.append(ImageMetadata.format.ilike(
                    f"%{query.image_format}%"))

            if query.min_resolution:
                filters.append(
                    (ImageMetadata.width * ImageMetadata.height) >= query.min_resolution
                )

            # Apply filters to query
            if filters:
                filtered_query = base_query.filter(and_(*filters))
            else:
                filtered_query = base_query

            # Get total count
            total_count = filtered_query.count()

            # Apply ordering, pagination
            results = filtered_query.order_by(
                desc(ImageMetadata.upload_date)
            ).offset(query.offset).limit(query.limit).all()

            return results, total_count

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error searching images: {str(e)}"
            )

    def get_student_image_stats(self, student_id: UUID) -> Dict[str, Any]:
        """Get image statistics for a student."""
        try:
            base_query = self.db.query(ImageMetadata).filter(
                ImageMetadata.student_id == student_id
            )

            total_images = base_query.count()
            processed_images = base_query.filter(
                ImageMetadata.is_processed == True
            ).count()

            failed_processing = base_query.filter(
                ImageMetadata.processing_error.isnot(None)
            ).count()

            # Average quality score
            quality_scores = [
                img.quality_score for img in base_query.all()
                if img.quality_score is not None
            ]
            avg_quality = sum(quality_scores) / \
                len(quality_scores) if quality_scores else None

            # Total storage used (in bytes)
            total_storage = sum([img.file_size for img in base_query.all()])

            return {
                "total_images": total_images,
                "processed_images": processed_images,
                "failed_processing": failed_processing,
                "processing_success_rate": processed_images / total_images if total_images > 0 else 0,
                "average_quality_score": avg_quality,
                "total_storage_bytes": total_storage,
                "total_storage_mb": round(total_storage / (1024 * 1024), 2)
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting image statistics: {str(e)}"
            )

    def cleanup_orphaned_metadata(self) -> int:
        """Clean up metadata records without corresponding meal records."""
        try:
            # This would require joining with meals table
            # For now, just return 0 as placeholder
            return 0

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error cleaning up orphaned metadata: {str(e)}"
            )

    def find_duplicate_images(self) -> List[Dict[str, Any]]:
        """Find images with duplicate file hashes."""
        try:
            from sqlalchemy import func

            # Find file hashes that appear more than once
            duplicate_hashes = self.db.query(
                ImageMetadata.file_hash,
                func.count(ImageMetadata.id).label('count')
            ).group_by(
                ImageMetadata.file_hash
            ).having(
                func.count(ImageMetadata.id) > 1
            ).all()

            duplicates = []
            for hash_info in duplicate_hashes:
                file_hash, count = hash_info
                images = self.db.query(ImageMetadata).filter(
                    ImageMetadata.file_hash == file_hash
                ).all()

                duplicates.append({
                    "file_hash": file_hash,
                    "count": count,
                    "images": [
                        {
                            "meal_id": str(img.meal_id),
                            "student_id": str(img.student_id),
                            "upload_date": img.upload_date,
                            "file_size": img.file_size
                        }
                        for img in images
                    ]
                })

            return duplicates

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error finding duplicate images: {str(e)}"
            )


def get_image_metadata_service(db: Session = None) -> ImageMetadataService:
    """Get image metadata service instance."""
    if db is None:
        db = next(get_db())
    return ImageMetadataService(db)
