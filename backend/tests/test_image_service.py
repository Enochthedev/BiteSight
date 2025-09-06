"""Tests for image processing and storage service."""

import os
import tempfile
import pytest
from uuid import uuid4
from pathlib import Path
from PIL import Image
from fastapi import UploadFile
from io import BytesIO

from app.services.image_service import ImageService


class TestImageService:
    """Test cases for ImageService."""

    @pytest.fixture
    def image_service(self):
        """Create ImageService instance with temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock settings for testing
            import app.core.config
            original_upload_dir = app.core.config.settings.UPLOAD_DIR
            app.core.config.settings.UPLOAD_DIR = temp_dir

            service = ImageService()
            yield service

            # Restore original settings
            app.core.config.settings.UPLOAD_DIR = original_upload_dir

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        image = Image.new('RGB', (640, 480), color='red')
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def small_image(self):
        """Create a small test image (below minimum resolution)."""
        image = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def dark_image(self):
        """Create a dark test image."""
        image = Image.new('RGB', (640, 480), color=(20, 20, 20))
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def bright_image(self):
        """Create a bright test image."""
        image = Image.new('RGB', (640, 480), color=(240, 240, 240))
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    def create_upload_file(self, image_bytes: BytesIO, filename: str = "test.jpg", content_type: str = "image/jpeg"):
        """Helper to create UploadFile from image bytes."""
        return UploadFile(
            file=image_bytes,
            filename=filename,
            headers={"content-type": content_type}
        )

    @pytest.mark.asyncio
    async def test_validate_valid_image(self, image_service, sample_image):
        """Test validation of a valid image."""
        upload_file = self.create_upload_file(sample_image)

        result = await image_service.validate_image(upload_file)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert "metadata" in result
        assert result["metadata"]["width"] == 640
        assert result["metadata"]["height"] == 480
        assert result["quality_score"] > 0

    @pytest.mark.asyncio
    async def test_validate_invalid_file_type(self, image_service):
        """Test validation with invalid file type."""
        text_content = BytesIO(b"This is not an image")
        upload_file = UploadFile(
            file=text_content,
            filename="test.txt",
            headers={"content-type": "text/plain"}
        )

        with pytest.raises(Exception):  # Should raise HTTPException
            await image_service.validate_image(upload_file)

    @pytest.mark.asyncio
    async def test_validate_small_image_warning(self, image_service, small_image):
        """Test validation warning for small image."""
        upload_file = self.create_upload_file(small_image)

        result = await image_service.validate_image(upload_file)

        assert result["is_valid"] is True
        assert len(result["quality_issues"]) > 0
        assert "resolution too low" in result["quality_issues"][0]

    @pytest.mark.asyncio
    async def test_validate_dark_image_warning(self, image_service, dark_image):
        """Test validation warning for dark image."""
        upload_file = self.create_upload_file(dark_image)

        result = await image_service.validate_image(upload_file)

        assert result["is_valid"] is True
        assert any("too dark" in warning for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_validate_bright_image_warning(self, image_service, bright_image):
        """Test validation warning for bright image."""
        upload_file = self.create_upload_file(bright_image)

        result = await image_service.validate_image(upload_file)

        assert result["is_valid"] is True
        assert any("too bright" in warning for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_save_image_success(self, image_service, sample_image):
        """Test successful image saving with organized structure."""
        upload_file = self.create_upload_file(sample_image)
        # Set file size manually since BytesIO doesn't have size attribute
        upload_file.size = len(sample_image.getvalue())
        meal_id = uuid4()

        result = await image_service.save_image(upload_file, meal_id)

        assert result["meal_id"] == str(meal_id)
        assert "raw_path" in result
        assert "processed_path" in result
        assert "thumbnail_path" in result
        assert "file_hash" in result
        assert result["file_size"] > 0

        # Check that files were actually created
        assert Path(result["raw_path"]).exists()
        if result["processed_path"]:
            assert Path(result["processed_path"]).exists()
        if result["thumbnail_path"]:
            assert Path(result["thumbnail_path"]).exists()

    def test_preprocess_image_resize(self, image_service, tmp_path):
        """Test image preprocessing and resizing."""
        # Create test image file
        image = Image.new('RGB', (640, 480), color='green')
        image_path = tmp_path / "test.jpg"
        image.save(image_path)

        processed = image_service.preprocess_image(str(image_path))

        assert processed is not None
        assert processed.size == (224, 224)
        assert processed.mode == 'RGB'

    def test_preprocess_image_convert_mode(self, image_service, tmp_path):
        """Test image preprocessing with mode conversion."""
        # Create RGBA image
        image = Image.new('RGBA', (300, 300), color=(255, 0, 0, 128))
        image_path = tmp_path / "test.png"
        image.save(image_path)

        processed = image_service.preprocess_image(str(image_path))

        assert processed is not None
        assert processed.mode == 'RGB'
        assert processed.size == (224, 224)

    def test_normalize_image_array(self, image_service):
        """Test image normalization to numpy array."""
        image = Image.new('RGB', (224, 224), color=(128, 128, 128))

        normalized = image_service.normalize_image_array(image)

        # Batch, Channels, Height, Width
        assert normalized.shape == (1, 3, 224, 224)
        assert normalized.dtype in ['float32', 'float64']
        # Check that normalization was applied (values should be around 0 for gray image)
        assert abs(normalized.mean()) < 1.0

    def test_get_image_metadata(self, image_service, tmp_path):
        """Test image metadata extraction."""
        image = Image.new('RGB', (800, 600), color='blue')
        image_path = tmp_path / "test.jpg"
        image.save(image_path)

        metadata = image_service.get_image_metadata(str(image_path))

        assert metadata["width"] == 800
        assert metadata["height"] == 600
        assert metadata["format"] == "JPEG"
        assert metadata["mode"] == "RGB"
        assert metadata["file_size"] > 0

    def test_get_organized_path(self, image_service):
        """Test organized path generation."""
        meal_id = uuid4()

        path = image_service._get_organized_path(meal_id, "raw", "jpg")

        assert str(meal_id) in str(path)
        assert "raw" in str(path)
        assert path.suffix == ".jpg"
        # Should contain date structure (YYYY/MM/DD)
        path_parts = path.parts
        assert len([p for p in path_parts if p.isdigit()
                   and len(p) == 4]) >= 1  # Year

    def test_get_image_paths(self, image_service, tmp_path):
        """Test image path retrieval."""
        meal_id = uuid4()

        # Create test files in organized structure
        raw_path = image_service._get_organized_path(meal_id, "raw", "jpg")
        raw_path.parent.mkdir(parents=True, exist_ok=True)

        # Create dummy image file
        image = Image.new('RGB', (100, 100), color='red')
        image.save(raw_path)

        paths = image_service.get_image_paths(meal_id)

        assert "raw" in paths
        assert paths["raw"] == str(raw_path)

    def test_delete_image(self, image_service, tmp_path):
        """Test image deletion."""
        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_text("test content")

        # Test successful deletion
        result = image_service.delete_image(str(test_file))
        assert result is True
        assert not test_file.exists()

        # Test deletion of non-existent file
        result = image_service.delete_image(str(test_file))
        assert result is False

    def test_delete_meal_images(self, image_service, tmp_path):
        """Test deletion of all meal images."""
        meal_id = uuid4()

        # Create test files
        raw_path = image_service._get_organized_path(meal_id, "raw", "jpg")
        processed_path = image_service._get_organized_path(
            meal_id, "processed", "jpg")

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        processed_path.parent.mkdir(parents=True, exist_ok=True)

        # Create dummy files
        raw_path.write_text("raw image")
        processed_path.write_text("processed image")

        results = image_service.delete_meal_images(meal_id)

        assert "raw" in results
        assert "processed" in results
        # Files should be deleted
        assert not raw_path.exists()
        assert not processed_path.exists()


class TestImageQualityValidation:
    """Test cases for image quality validation."""

    def test_aspect_ratio_validation(self):
        """Test aspect ratio validation logic."""
        service = ImageService()

        # Normal aspect ratio
        normal_image = Image.new('RGB', (640, 480))  # 4:3 ratio
        result = service._validate_image_quality(normal_image)
        assert len([w for w in result["warnings"] if "aspect ratio" in w]) == 0

        # Extreme aspect ratio
        extreme_image = Image.new('RGB', (1000, 200))  # 5:1 ratio
        result = service._validate_image_quality(extreme_image)
        assert len([w for w in result["warnings"] if "aspect ratio" in w]) > 0

    def test_resolution_validation(self):
        """Test resolution validation logic."""
        service = ImageService()

        # Low resolution
        low_res_image = Image.new('RGB', (100, 100))
        result = service._validate_image_quality(low_res_image)
        assert len(result["quality_issues"]) > 0
        assert "resolution too low" in result["quality_issues"][0]

        # Good resolution
        good_res_image = Image.new('RGB', (640, 480))
        result = service._validate_image_quality(good_res_image)
        resolution_issues = [
            issue for issue in result["quality_issues"] if "resolution" in issue]
        assert len(resolution_issues) == 0

    def test_brightness_validation(self):
        """Test brightness validation logic."""
        service = ImageService()

        # Dark image
        dark_image = Image.new('RGB', (300, 300), color=(20, 20, 20))
        result = service._validate_image_quality(dark_image)
        dark_warnings = [w for w in result["warnings"] if "too dark" in w]
        assert len(dark_warnings) > 0

        # Bright image
        bright_image = Image.new('RGB', (300, 300), color=(240, 240, 240))
        result = service._validate_image_quality(bright_image)
        bright_warnings = [w for w in result["warnings"] if "too bright" in w]
        assert len(bright_warnings) > 0

        # Normal brightness
        normal_image = Image.new('RGB', (300, 300), color=(128, 128, 128))
        result = service._validate_image_quality(normal_image)
        brightness_warnings = [w for w in result["warnings"]
                               if "too dark" in w or "too bright" in w]
        assert len(brightness_warnings) == 0
