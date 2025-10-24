"""
Unit tests for core utility functions
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.core.utils import create_audit_log, get_setting, set_setting
import json


class TestAuditLog:
    """Tests for audit log creation"""
    
    def test_create_audit_log_with_user(self):
        """Test creating audit log with user"""
        # Mock database
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        # Create audit log
        create_audit_log(
            db=mock_db,
            contact_id=123,
            user=mock_user,
            action="create",
            entity_type="contact",
            changes={"name": "Test"}
        )
        
        # Verify
        assert mock_db.add.called
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.contact_id == 123
        assert audit_entry.user_id == 1
        assert audit_entry.username == "testuser"
        assert audit_entry.action == "create"
        assert audit_entry.entity_type == "contact"
    
    def test_create_audit_log_without_user(self):
        """Test creating audit log without user"""
        mock_db = Mock()
        
        create_audit_log(
            db=mock_db,
            contact_id=123,
            user=None,
            action="delete",
            entity_type="contact"
        )
        
        assert mock_db.add.called
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.user_id is None
        assert audit_entry.username is None
    
    def test_create_audit_log_with_changes(self):
        """Test creating audit log with changes dict"""
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        changes = {"field": "value", "old": "old_value", "new": "new_value"}
        
        create_audit_log(
            db=mock_db,
            contact_id=123,
            user=mock_user,
            action="update",
            changes=changes
        )
        
        assert mock_db.add.called
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.changes is not None
        # Changes should be JSON string
        parsed = json.loads(audit_entry.changes)
        assert parsed["field"] == "value"


class TestSettings:
    """Tests for app settings"""
    
    def test_get_setting_exists(self):
        """Test getting existing setting"""
        # Mock database
        mock_db = Mock()
        mock_setting = Mock()
        mock_setting.value = "test_value"
        mock_db.query().filter().first.return_value = mock_setting
        
        # Get setting
        result = get_setting(mock_db, "test_key")
        
        # Verify
        assert result == "test_value"
    
    def test_get_setting_not_exists(self):
        """Test getting non-existent setting"""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None
        
        result = get_setting(mock_db, "nonexistent")
        
        assert result is None
    
    def test_get_setting_with_default(self):
        """Test getting non-existent setting with default"""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None
        
        result = get_setting(mock_db, "nonexistent", default="default_value")
        
        assert result == "default_value"
    
    def test_set_setting_new(self):
        """Test setting new setting"""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None
        
        set_setting(mock_db, "new_key", "new_value")
        
        assert mock_db.add.called
        setting = mock_db.add.call_args[0][0]
        assert setting.key == "new_key"
        assert setting.value == "new_value"
    
    def test_set_setting_update_existing(self):
        """Test updating existing setting"""
        mock_db = Mock()
        mock_setting = Mock()
        mock_setting.key = "existing_key"
        mock_setting.value = "old_value"
        mock_db.query().filter().first.return_value = mock_setting
        
        set_setting(mock_db, "existing_key", "new_value")
        
        assert mock_setting.value == "new_value"
        assert not mock_db.add.called  # Should not add, only update
    
    def test_set_setting_none_value(self):
        """Test setting None value"""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None
        
        set_setting(mock_db, "key", None)
        
        assert mock_db.add.called
        setting = mock_db.add.call_args[0][0]
        assert setting.value is None

