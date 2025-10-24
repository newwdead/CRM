"""
Unit tests for Celery tasks
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io


class TestOCRTask:
    """Tests for process_ocr_task"""
    
    @patch('app.tasks.SessionLocal')
    @patch('app.tasks.OCRManager')
    def test_process_ocr_task_success(self, mock_ocr_manager, mock_session):
        """Test successful OCR processing"""
        from app.tasks import process_ocr_task
        
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)
        
        # Mock contact
        mock_contact = Mock()
        mock_contact.id = 1
        mock_contact.image_path = "test.jpg"
        mock_db.query().filter().first.return_value = mock_contact
        
        # Mock OCR result
        mock_ocr = Mock()
        mock_ocr_manager.return_value = mock_ocr
        mock_ocr.extract_text.return_value = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
        
        # Execute task
        result = process_ocr_task(1, "auto")
        
        # Verify
        assert result["status"] == "success"
        assert "contact_id" in result
        
    @patch('app.tasks.SessionLocal')
    def test_process_ocr_task_contact_not_found(self, mock_session):
        """Test OCR processing when contact doesn't exist"""
        from app.tasks import process_ocr_task
        
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)
        
        # Contact not found
        mock_db.query().filter().first.return_value = None
        
        # Execute task
        result = process_ocr_task(999, "auto")
        
        # Verify
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestDuplicateDetectionTask:
    """Tests for find_duplicates_task"""
    
    @patch('app.tasks.SessionLocal')
    @patch('app.tasks.find_duplicates_for_contact')
    def test_find_duplicates_task_success(self, mock_find_duplicates, mock_session):
        """Test successful duplicate detection"""
        from app.tasks import find_duplicates_task
        
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)
        
        # Mock contact
        mock_contact = Mock()
        mock_contact.id = 1
        mock_db.query().filter().first.return_value = mock_contact
        
        # Mock duplicates found
        mock_find_duplicates.return_value = [
            {"contact_id": 2, "similarity": 0.85}
        ]
        
        # Execute task
        result = find_duplicates_task(1, 0.7)
        
        # Verify
        assert result["status"] == "success"
        assert result["duplicates_found"] == 1
    
    @patch('app.tasks.SessionLocal')
    def test_find_duplicates_task_contact_not_found(self, mock_session):
        """Test duplicate detection when contact doesn't exist"""
        from app.tasks import find_duplicates_task
        
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)
        
        # Contact not found
        mock_db.query().filter().first.return_value = None
        
        # Execute task
        result = find_duplicates_task(999, 0.7)
        
        # Verify
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()


class TestImageProcessingTask:
    """Tests for process_thumbnail_task"""
    
    @patch('app.tasks.SessionLocal')
    @patch('app.tasks.Image')
    @patch('app.tasks.os.path.exists')
    def test_process_thumbnail_task_success(self, mock_exists, mock_image_class, mock_session):
        """Test successful thumbnail creation"""
        from app.tasks import process_thumbnail_task
        
        # Mock filesystem
        mock_exists.return_value = True
        
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)
        
        # Mock contact
        mock_contact = Mock()
        mock_contact.id = 1
        mock_contact.image_path = "test.jpg"
        mock_db.query().filter().first.return_value = mock_contact
        
        # Mock PIL Image
        mock_img = Mock()
        mock_image_class.open.return_value = mock_img
        mock_img.thumbnail = Mock()
        mock_img.save = Mock()
        
        # Execute task
        result = process_thumbnail_task(1)
        
        # Verify
        assert result["status"] == "success"
        mock_img.thumbnail.assert_called_once()
        mock_img.save.assert_called_once()
    
    @patch('app.tasks.SessionLocal')
    def test_process_thumbnail_task_contact_not_found(self, mock_session):
        """Test thumbnail creation when contact doesn't exist"""
        from app.tasks import process_thumbnail_task
        
        # Mock database
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)
        
        # Contact not found
        mock_db.query().filter().first.return_value = None
        
        # Execute task
        result = process_thumbnail_task(999)
        
        # Verify
        assert result["status"] == "error"


class TestBackupTask:
    """Tests for create_backup_task"""
    
    @patch('app.tasks.subprocess.run')
    @patch('app.tasks.os.getenv')
    def test_create_backup_task_success(self, mock_getenv, mock_subprocess):
        """Test successful database backup"""
        from app.tasks import create_backup_task
        
        # Mock environment
        mock_getenv.return_value = "postgresql://user:pass@localhost/db"
        
        # Mock subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Execute task
        result = create_backup_task()
        
        # Verify
        assert result["status"] == "success"
        assert "backup_path" in result
        mock_subprocess.assert_called_once()
    
    @patch('app.tasks.subprocess.run')
    def test_create_backup_task_failure(self, mock_subprocess):
        """Test backup failure"""
        from app.tasks import create_backup_task
        
        # Mock subprocess failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Backup failed"
        mock_subprocess.return_value = mock_result
        
        # Execute task
        result = create_backup_task()
        
        # Verify
        assert result["status"] == "error"

