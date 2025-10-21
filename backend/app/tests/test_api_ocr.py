"""
Tests for OCR API endpoints
"""
import pytest
from fastapi import status
import io


class TestOCREndpoints:
    """Test suite for /ocr endpoints"""
    
    def test_get_ocr_providers(self, client):
        """Test getting available OCR providers (no auth required)"""
        response = client.get("/ocr/providers")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "available" in data
        assert "details" in data
        assert isinstance(data["available"], list)
    
    def test_upload_without_auth(self, client):
        """Test that upload requires authentication"""
        # Create a fake image file
        files = {"file": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")}
        response = client.post("/ocr/upload/", files=files)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_upload_non_image_file(self, client, auth_token):
        """Test that non-image files are rejected"""
        files = {"file": ("test.txt", io.BytesIO(b"text data"), "text/plain")}
        response = client.post(
            "/ocr/upload/",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "must be an image" in response.json()["detail"].lower()
    
    def test_batch_upload_without_auth(self, client):
        """Test that batch upload requires authentication"""
        files = {"file": ("test.zip", io.BytesIO(b"fake zip data"), "application/zip")}
        response = client.post("/ocr/batch-upload/", files=files)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_batch_upload_non_zip_file(self, client, auth_token):
        """Test that non-ZIP files are rejected for batch upload"""
        files = {"file": ("test.jpg", io.BytesIO(b"image data"), "image/jpeg")}
        response = client.post(
            "/ocr/batch-upload/",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "zip" in response.json()["detail"].lower()
    
    def test_get_batch_status_without_auth(self, client):
        """Test that batch status check requires authentication"""
        response = client.get("/ocr/batch-status/fake-task-id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_batch_status_with_auth(self, client, auth_token):
        """Test getting batch status with authentication"""
        # This will likely return PENDING or error for a fake task ID
        response = client.get(
            "/ocr/batch-status/fake-task-id-12345",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 with task state info (even if task doesn't exist)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "task_id" in data
        assert "state" in data


class TestOCRUploadValidation:
    """Test suite for OCR upload validation"""
    
    def test_upload_with_invalid_provider(self, client, auth_token):
        """Test upload with invalid OCR provider"""
        files = {"file": ("test.jpg", io.BytesIO(b"fake image"), "image/jpeg")}
        response = client.post(
            "/ocr/upload/?provider=invalid_provider",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # FastAPI query validation should reject invalid enum
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_upload_with_valid_provider(self, client, auth_token):
        """Test upload with valid OCR provider (will fail on image processing)"""
        files = {"file": ("test.jpg", io.BytesIO(b"fake image"), "image/jpeg")}
        response = client.post(
            "/ocr/upload/?provider=tesseract",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Will fail because it's not a real image, but provider validation passes
        # Expected to return 500 or 400 depending on where it fails
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

