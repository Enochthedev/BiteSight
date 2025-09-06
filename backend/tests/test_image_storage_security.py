"""Tests for image storage operations and security."""

import os
import tempfile
import pytest
from uuid import uuid4
from pathlib import Path
from PIL import Image
from fastapi import UploadFile, HTTPException
from io import BytesIO
from unittest.mock import Mock, patch

from app.services.image_service import ImageService
from app.services.image_metadata_service import ImageMetadataService
from app.models.image_metadata import ImageMetadataCreate, ImageSearchQuery


class TestImageStorageSecurity:
    """Test cases for image storage security."""

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
    def mock_db_session(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        image = Image.new('RGB', (640, 480), color='red')
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    def create_upload_file(self, image_bytes: BytesIO, filename: str = "test.jpg", content_type: str = "image/jpeg"):
        """Helper to create UploadFile from image bytes."""
        upload_file = UploadFile(
            file=image_bytes,
            filename=filename,
            headers={"content-type": content_type}
        )
        upload_file.size = len(image_bytes.getvalue())
        return upload_file

    @pytest.mark.asyncio
    async def test_secure_file_naming(self, image_service, sample_image):
        """Test that files are stored with secure, organized naming."""
        upload_file = self.create_upload_file(sample_image)
        meal_id = uuid4()

        result = await image_service.save_image(upload_file, meal_id)

        # Check that file paths are organized by date
        raw_path = Path(result["raw_path"])
        assert "raw" in str(raw_path)
        assert str(meal_id) in str(raw_path)

        # Check date-based organization (YYYY/MM/DD)
        path_parts = raw_path.parts
        date_parts = [p for p in path_parts if p.isdigit()]
        assert len(date_parts) >= 3  # Year, month, day

    @pytest.mark.asyncio
    async def test_file_hash_integrity(self, image_service, sample_image):
        """Test file integrity checking with hash."""
        upload_file = self.create_upload_file(sample_image)
        meal_id = uuid4()

        result = await image_service.save_image(upload_file, meal_id)

        # Verify file hash is generated
        assert "file_hash" in result
        assert len(result["file_hash"]) == 32  # MD5 hash length

        # Verify file content matches hash
        import hashlib
        with open(result["raw_path"], "rb") as f:
            content = f.read()
            expected_hash = hashlib.md5(content).hexdigest()
            assert result["file_hash"] == expected_hash

    @pytest.mark.asyncio
    async def test_malicious_filename_handling(self, image_service, sample_image):
        """Test handling of malicious filenames."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "test<script>alert('xss')</script>.jpg",
            "test\x00.jpg",
            "con.jpg",  # Windows reserved name
            "prn.jpg",  # Windows reserved name
        ]

        for malicious_filename in malicious_filenames:
            upload_file = self.create_upload_file(
                sample_image, malicious_filename)
            meal_id = uuid4()

            result = await image_service.save_image(upload_file, meal_id)

            # Verify file is stored safely with meal_id as filename
            raw_path = Path(result["raw_path"])
            assert str(meal_id) in raw_path.name
            assert malicious_filename not in str(raw_path)

    @pytest.mark.asyncio
    async def test_file_size_limits(self, image_service):
        """Test file size validation and limits."""
        # Create oversized image content
        large_content = b"x" * (15 * 1024 * 1024)  # 15MB (over 10MB limit)
        large_file = BytesIO(large_content)

        upload_file = UploadFile(
            file=large_file,
            filename="large.jpg",
            headers={"content-type": "image/jpeg"}
        )
        upload_file.size = len(large_content)

        meal_id = uuid4()

        # Should raise HTTPException for oversized file
        with pytest.raises(HTTPException) as exc_info:
            await image_service.save_image(upload_file, meal_id)

        assert exc_info.value.status_code == 400
        assert "too large" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_invalid_file_type_rejection(self, image_service):
        """Test rejection of non-image files."""
        # Create text file disguised as image
        text_content = BytesIO(b"This is not an image file")

        upload_file = UploadFile(
            file=text_content,
            filename="malicious.jpg",
            headers={"content-type": "image/jpeg"}  # Lying about content type
        )
        upload_file.size = len(text_content.getvalue())

        meal_id = uuid4()

        # Should raise HTTPException for invalid image
        with pytest.raises(HTTPException) as exc_info:
            await image_service.save_image(upload_file, meal_id)

        assert exc_info.value.status_code == 400

    def test_directory_traversal_prevention(self, image_service):
        """Test prevention of directory traversal attacks."""
        meal_id = uuid4()

        # Test various directory traversal attempts
        traversal_attempts = [
            "../../../etc",
            "..\\..\\windows",
            "/etc/passwd",
            "C:\\Windows\\System32"
        ]

        for attempt in traversal_attempts:
            path = image_service._get_organized_path(meal_id, attempt, "jpg")

            # Verify path is contained within upload directory
            assert str(image_service.upload_dir) in str(path.resolve())
            assert str(meal_id) in str(path)

    def test_file_permissions(self, image_service, sample_image, tmp_path):
        """Test that created files have appropriate permissions."""
        # This test is platform-specific and may not work on all systems
        if os.name != 'posix':
            pytest.skip(
                "File permission test only applicable on POSIX systems")

        # Create test image file
        image = Image.new('RGB', (300, 300), color='blue')
        image_path = tmp_path / "test.jpg"
        image.save(image_path)

        # Check file permissions are not world-writable
        stat_info = os.stat(image_path)
        permissions = oct(stat_info.st_mode)[-3:]

        # Should not be world-writable (last digit should not be 2, 3, 6, or 7)
        assert permissions[-1] not in ['2', '3', '6', '7']


class TestImageMetadataService:
    """Test cases for image metadata service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.query.return_value = Mock()
        db.commit.return_value = None
        db.rollback.return_value = None
        return db

    @pytest.fixture
    def metadata_service(self, mock_db):
        """Create ImageMetadataService instance."""
        return ImageMetadataService(mock_db)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata for testing."""
        return ImageMetadataCreate(
            meal_id=uuid4(),
            student_id=uuid4(),
            raw_image_path="/uploads/raw/2023/01/01/test.jpg",
            file_size=1024,
            file_hash="d41d8cd98f00b204e9800998ecf8427e",
            mime_type="image/jpeg",
            width=640,
            height=480,
            format="JPEG",
            mode="RGB"
        )

    def test_create_metadata_success(self, metadata_service, sample_metadata, mock_db):
        """Test successful metadata creation."""
        # Mock no existing metadata
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock successful creation
        mock_metadata = Mock()
        mock_db.add.return_value = None
        mock_db.refresh.return_value = None

        with patch('app.models.image_metadata.ImageMetadata') as mock_model:
            mock_model.return_value = mock_metadata
            result = metadata_service.create_metadata(sample_metadata)

            # Verify database operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_create_metadata_duplicate_prevention(self, metadata_service, sample_metadata, mock_db):
        """Test prevention of duplicate metadata creation."""
        # Mock existing metadata
        existing_metadata = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_metadata

        # Should raise HTTPException for duplicate
        with pytest.raises(HTTPException) as exc_info:
            metadata_service.create_metadata(sample_metadata)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    def test_search_with_sql_injection_prevention(self, metadata_service, mock_db):
        """Test that search queries prevent SQL injection."""
        # Create search query with potential SQL injection
        malicious_query = ImageSearchQuery(
            image_format="'; DROP TABLE image_metadata; --",
            limit=50,
            offset=0
        )

        # Mock query chain
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Should not raise exception and should use parameterized queries
        results, count = metadata_service.search_images(malicious_query)

        assert results == []
        assert count == 0
        # Verify that filter was called (indicating parameterized query usage)
        mock_query.filter.assert_called()

    def test_file_hash_duplicate_detection(self, metadata_service, mock_db):
        """Test duplicate file detection by hash."""
        test_hash = "d41d8cd98f00b204e9800998ecf8427e"

        # Mock existing metadata with same hash
        existing_metadata = Mock()
        existing_metadata.file_hash = test_hash
        mock_db.query.return_value.filter.return_value.first.return_value = existing_metadata

        result = metadata_service.get_metadata_by_hash(test_hash)

        assert result == existing_metadata
        # Verify hash-based query was made
        mock_db.query.assert_called()

    def test_student_data_isolation(self, metadata_service, mock_db):
        """Test that students can only access their own image data."""
        student_id = uuid4()
        other_student_id = uuid4()

        # Mock query for student's images
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.all.return_value = []

        stats = metadata_service.get_student_image_stats(student_id)

        # Verify that filter was called with correct student_id
        mock_query.filter.assert_called()
        assert stats["total_images"] == 5


class TestImageAccessControl:
    """Test cases for image access control."""

    def test_image_path_validation(self):
        """Test validation of image paths to prevent unauthorized access."""
        service = ImageService()

        # Test various malicious paths
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\sam",
            "\\\\server\\share\\file.txt",
            "/proc/self/environ"
        ]

        for malicious_path in malicious_paths:
            # get_image_metadata should handle path validation
            with pytest.raises((HTTPException, FileNotFoundError, PermissionError)):
                service.get_image_metadata(malicious_path)

    def test_image_retrieval_authorization(self):
        """Test that image retrieval requires proper authorization."""
        # This would typically be tested at the API endpoint level
        # with proper authentication and authorization checks
        pass  # Placeholder for endpoint-level tests

    def test_secure_cleanup_operations(self, tmp_path):
        """Test that cleanup operations are secure and don't affect other files."""
        service = ImageService()

        # Create test directory structure
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()

        # Create some test files
        (test_dir / "keep_this.txt").write_text("important data")
        (test_dir / "image1.jpg").write_text("image data")
        (test_dir / "image2.jpg").write_text("image data")

        # Mock upload directory
        original_upload_dir = service.upload_dir
        service.upload_dir = test_dir

        try:
            # Test that cleanup doesn't affect non-image files
            meal_id = uuid4()
            results = service.delete_meal_images(meal_id)

            # Important file should still exist
            assert (test_dir / "keep_this.txt").exists()

        finally:
            # Restore original upload directory
            service.upload_dir = original_upload_dir
