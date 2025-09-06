"""Image processing and storage service."""

from typing import Optional, Tuple, Dict, Any
from uuid import UUID
import os
import hashlib
from pathlib import Path
from datetime import datetime
import numpy as np

from PIL import Image, ImageStat, ExifTags
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.models.image_metadata import ImageMetadataCreate
from app.services.image_metadata_service import ImageMetadataService


class ImageService:
    """Service for handling image upload, processing, and storage."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

        # Create organized subdirectories
        self.raw_dir = self.upload_dir / "raw"
        self.processed_dir = self.upload_dir / "processed"
        self.thumbnails_dir = self.upload_dir / "thumbnails"

        for directory in [self.raw_dir, self.processed_dir, self.thumbnails_dir]:
            directory.mkdir(exist_ok=True)

    def _get_organized_path(self, meal_id: UUID, subdirectory: str, extension: str = "jpg") -> Path:
        """Generate organized file path based on date and meal ID."""
        # Sanitize subdirectory to prevent directory traversal
        import os
        safe_subdirectory = os.path.basename(subdirectory)

        # Only allow specific subdirectories
        allowed_subdirs = ["raw", "processed", "thumbnails"]
        if safe_subdirectory not in allowed_subdirs:
            safe_subdirectory = "raw"  # Default to raw if invalid

        date_str = datetime.now().strftime("%Y/%m/%d")
        date_path = self.upload_dir / safe_subdirectory / date_str
        date_path.mkdir(parents=True, exist_ok=True)
        return date_path / f"{meal_id}.{extension}"

    async def validate_image(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded image file and return validation results."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metadata": {}
        }

        # Check file type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            validation_results["is_valid"] = False
            validation_results["errors"].append(
                f"Invalid file type '{file.content_type}'. Allowed types: {settings.ALLOWED_IMAGE_TYPES}"
            )

        # Check file size
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            validation_results["is_valid"] = False
            validation_results["errors"].append(
                f"File too large ({file.size} bytes). Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
            )

        # Read file content for quality validation
        try:
            content = await file.read()
            file_size = len(content)
            await file.seek(0)  # Reset file pointer

            # Validate image can be opened
            try:
                image = Image.open(file.file)
                validation_results["metadata"]["width"] = image.width
                validation_results["metadata"]["height"] = image.height
                validation_results["metadata"]["format"] = image.format
                validation_results["metadata"]["mode"] = image.mode

                # Check image quality
                quality_results = self._validate_image_quality(image)
                validation_results.update(quality_results)

            except Exception as e:
                validation_results["is_valid"] = False
                validation_results["errors"].append(
                    f"Invalid image file: {str(e)}")

        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(
                f"Error reading file: {str(e)}")

        if not validation_results["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Image validation failed",
                    "errors": validation_results["errors"],
                    "warnings": validation_results["warnings"]
                }
            )

        return validation_results

    def _validate_image_quality(self, image: Image.Image) -> Dict[str, Any]:
        """Validate image quality for food recognition."""
        quality_results = {
            "quality_score": 0.0,
            "quality_issues": [],
            "warnings": []
        }

        # Check minimum resolution
        min_width, min_height = 224, 224  # Minimum for MobileNetV2
        if image.width < min_width or image.height < min_height:
            quality_results["quality_issues"].append(
                f"Image resolution too low ({image.width}x{image.height}). "
                f"Minimum recommended: {min_width}x{min_height}"
            )

        # Check aspect ratio (should be reasonable for food photos)
        aspect_ratio = image.width / image.height
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            quality_results["warnings"].append(
                f"Unusual aspect ratio ({aspect_ratio:.2f}). Food photos work best with ratios between 0.5 and 2.0"
            )

        # Check if image is too dark or too bright
        if image.mode in ['RGB', 'L']:
            try:
                stat = ImageStat.Stat(image)
                if image.mode == 'RGB':
                    brightness = sum(stat.mean) / 3
                else:
                    brightness = stat.mean[0]

                if brightness < 50:
                    quality_results["warnings"].append(
                        "Image appears too dark. Consider retaking with better lighting.")
                elif brightness > 200:
                    quality_results["warnings"].append(
                        "Image appears too bright. Consider retaking with less exposure.")

                # Calculate quality score based on brightness and resolution
                brightness_score = min(1.0, max(0.0, (brightness - 30) / 170))
                resolution_score = min(
                    1.0, (image.width * image.height) / (640 * 480))
                quality_results["quality_score"] = (
                    brightness_score + resolution_score) / 2

            except Exception:
                quality_results["warnings"].append(
                    "Could not analyze image brightness")

        return quality_results

    async def save_image(self, file: UploadFile, meal_id: UUID, student_id: UUID = None, db_session=None) -> Dict[str, Any]:
        """Save uploaded image to storage with organized structure and metadata."""
        validation_results = await self.validate_image(file)

        # Generate organized file paths - sanitize filename
        safe_extension = "jpg"  # Default extension
        if file.filename:
            # Extract only the extension, ignore path components
            import os
            base_name = os.path.basename(file.filename)
            if '.' in base_name:
                ext = base_name.split('.')[-1].lower()
                # Only allow safe image extensions
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                    safe_extension = ext

        raw_path = self._get_organized_path(meal_id, "raw", safe_extension)
        processed_path = self._get_organized_path(meal_id, "processed", "jpg")
        thumbnail_path = self._get_organized_path(meal_id, "thumbnails", "jpg")

        # Reset file pointer and read content
        await file.seek(0)
        content = await file.read()

        # Save raw image
        with open(raw_path, "wb") as buffer:
            buffer.write(content)

        # Generate file hash for integrity checking
        file_hash = hashlib.md5(content).hexdigest()

        # Create processed version and thumbnail
        processing_error = None
        try:
            processed_image = self.preprocess_image(str(raw_path))
            if processed_image:
                processed_image.save(processed_path, "JPEG", quality=85)

                # Create thumbnail (150x150)
                thumbnail = processed_image.copy()
                thumbnail.thumbnail((150, 150), Image.Resampling.LANCZOS)
                thumbnail.save(thumbnail_path, "JPEG", quality=80)
        except Exception as e:
            # If preprocessing fails, we still have the raw image
            processing_error = str(e)
            print(f"Warning: Could not create processed version: {e}")

        # Save metadata to database if session provided
        if db_session and student_id:
            try:
                metadata_service = ImageMetadataService(db_session)
                metadata = ImageMetadataCreate(
                    meal_id=meal_id,
                    student_id=student_id,
                    raw_image_path=str(raw_path),
                    processed_image_path=str(
                        processed_path) if processed_path.exists() else None,
                    thumbnail_path=str(
                        thumbnail_path) if thumbnail_path.exists() else None,
                    original_filename=file.filename,
                    file_size=len(content),
                    file_hash=file_hash,
                    mime_type=file.content_type or "image/jpeg",
                    width=validation_results["metadata"]["width"],
                    height=validation_results["metadata"]["height"],
                    format=validation_results["metadata"]["format"],
                    mode=validation_results["metadata"]["mode"],
                    quality_score=int(validation_results.get(
                        "quality_score", 0) * 100),
                    quality_issues=validation_results.get(
                        "quality_issues", []),
                    quality_warnings=validation_results.get("warnings", []),
                    exif_data=validation_results["metadata"].get("exif", {}),
                    is_processed=processed_path.exists() and not processing_error,
                    processing_error=processing_error
                )
                metadata_service.create_metadata(metadata)
            except Exception as e:
                print(f"Warning: Could not save image metadata: {e}")

        return {
            "meal_id": str(meal_id),
            "raw_path": str(raw_path),
            "processed_path": str(processed_path) if processed_path.exists() else None,
            "thumbnail_path": str(thumbnail_path) if thumbnail_path.exists() else None,
            "file_hash": file_hash,
            "file_size": len(content),
            "validation_results": validation_results
        }

    def preprocess_image(self, image_path: str, target_size: Tuple[int, int] = (224, 224)) -> Optional[Image.Image]:
        """Preprocess image for AI model inference with normalization."""
        try:
            image = Image.open(image_path)

            # Handle EXIF orientation
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = image._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation)
                    if orientation_value == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation_value == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation_value == 8:
                        image = image.rotate(90, expand=True)
            except (AttributeError, KeyError, TypeError):
                # No EXIF data or orientation info
                pass

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize to model input size while maintaining aspect ratio
            image.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Create a new image with the exact target size and paste the resized image
            processed_image = Image.new('RGB', target_size, (255, 255, 255))

            # Calculate position to center the image
            x_offset = (target_size[0] - image.width) // 2
            y_offset = (target_size[1] - image.height) // 2
            processed_image.paste(image, (x_offset, y_offset))

            return processed_image
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error preprocessing image: {str(e)}"
            )

    def normalize_image_array(self, image: Image.Image) -> np.ndarray:
        """Convert PIL image to normalized numpy array for model input."""
        # Convert to numpy array
        img_array = np.array(image, dtype=np.float32)

        # Normalize to [0, 1] range
        img_array = img_array / 255.0

        # Apply ImageNet normalization (standard for MobileNetV2)
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_array = (img_array - mean) / std

        # Add batch dimension and transpose to CHW format
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)

        return img_array

    def get_image_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract metadata from image file."""
        try:
            image = Image.open(image_path)
            metadata = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "file_size": os.path.getsize(image_path)
            }

            # Extract EXIF data if available
            try:
                exif_data = image._getexif()
                if exif_data:
                    metadata["exif"] = {
                        ExifTags.TAGS.get(k, k): v
                        for k, v in exif_data.items()
                        if k in ExifTags.TAGS
                    }
            except (AttributeError, KeyError):
                metadata["exif"] = {}

            return metadata
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading image metadata: {str(e)}"
            )

    def get_image_paths(self, meal_id: UUID) -> Dict[str, Optional[str]]:
        """Get all image paths for a meal ID."""
        paths = {}

        # Search for images in organized structure
        date_patterns = [
            datetime.now().strftime("%Y/%m/%d"),
        ]

        # Add yesterday's date if not the first day of month
        if datetime.now().day > 1:
            yesterday = datetime.now().replace(day=datetime.now().day-1)
            date_patterns.append(yesterday.strftime("%Y/%m/%d"))

        for img_type in ["raw", "processed", "thumbnails"]:
            paths[img_type] = None
            for date_pattern in date_patterns:
                for ext in ["jpg", "jpeg", "png"]:
                    potential_path = self.upload_dir / img_type / \
                        date_pattern / f"{meal_id}.{ext}"
                    if potential_path.exists():
                        paths[img_type] = str(potential_path)
                        break
                if paths[img_type]:
                    break

        return paths

    def delete_image(self, image_path: str) -> bool:
        """Delete image from storage."""
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception:
            return False

    def delete_meal_images(self, meal_id: UUID) -> Dict[str, bool]:
        """Delete all images associated with a meal."""
        paths = self.get_image_paths(meal_id)
        results = {}

        for img_type, path in paths.items():
            if path:
                results[img_type] = self.delete_image(path)
            else:
                results[img_type] = True  # Nothing to delete

        return results

    def cleanup_old_images(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up images older than specified days."""
        cutoff_date = datetime.now().replace(day=datetime.now().day - days_old)
        deleted_count = {"raw": 0, "processed": 0, "thumbnails": 0}

        for img_type in ["raw", "processed", "thumbnails"]:
            type_dir = self.upload_dir / img_type
            if type_dir.exists():
                for year_dir in type_dir.iterdir():
                    if year_dir.is_dir():
                        for month_dir in year_dir.iterdir():
                            if month_dir.is_dir():
                                for day_dir in month_dir.iterdir():
                                    if day_dir.is_dir():
                                        try:
                                            dir_date = datetime.strptime(
                                                f"{year_dir.name}/{month_dir.name}/{day_dir.name}",
                                                "%Y/%m/%d"
                                            )
                                            if dir_date < cutoff_date:
                                                for img_file in day_dir.iterdir():
                                                    if img_file.is_file():
                                                        img_file.unlink()
                                                        deleted_count[img_type] += 1
                                                # Remove empty directory
                                                if not any(day_dir.iterdir()):
                                                    day_dir.rmdir()
                                        except ValueError:
                                            # Invalid date format, skip
                                            continue

        return deleted_count


image_service = ImageService()
