"""
Tests for Repository Layer
Testing all repositories (Contact, Duplicate, User, OCR, Settings, Audit)
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Contact, User, OCRCorrection, AppSetting, AuditLog
from app.repositories import (
    ContactRepository,
    UserRepository,
    OCRRepository,
    SettingsRepository,
    AuditRepository
)


class TestContactRepository:
    """Tests for ContactRepository"""
    
    def test_create_contact(self, db: Session):
        """Test creating a contact"""
        repo = ContactRepository(db)
        
        contact_data = {
            'uid': 'test-uid-123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'company': 'Test Company'
        }
        
        contact = repo.create(contact_data)
        repo.commit()
        
        assert contact.id is not None
        assert contact.first_name == 'John'
        assert contact.email == 'john@example.com'
    
    def test_get_contact_by_id(self, db: Session, test_contact: Contact):
        """Test getting contact by ID"""
        repo = ContactRepository(db)
        
        found = repo.find_by_id(test_contact.id)
        
        assert found is not None
        assert found.id == test_contact.id
        assert found.first_name == test_contact.first_name
    
    def test_get_contact_by_uid(self, db: Session, test_contact: Contact):
        """Test getting contact by UID"""
        repo = ContactRepository(db)
        
        found = repo.find_by_uid(test_contact.uid)
        
        assert found is not None
        assert found.uid == test_contact.uid
    
    def test_update_contact(self, db: Session, test_contact: Contact):
        """Test updating a contact"""
        repo = ContactRepository(db)
        
        updated = repo.update(test_contact, {'first_name': 'Jane'})
        repo.commit()
        
        assert updated.first_name == 'Jane'
    
    def test_delete_contact(self, db: Session, test_contact: Contact):
        """Test deleting a contact"""
        repo = ContactRepository(db)
        
        contact_id = test_contact.id
        repo.delete(test_contact)
        repo.commit()
        
        found = repo.find_by_id(contact_id)
        assert found is None
    
    def test_count_contacts(self, db: Session, test_contact: Contact):
        """Test counting contacts"""
        repo = ContactRepository(db)
        
        count = repo.count()
        assert count >= 1
    
    def test_search_and_filter_contacts(self, db: Session, test_contact: Contact):
        """Test search and filter"""
        repo = ContactRepository(db)
        
        # Search by name
        results = repo.search(search_term=test_contact.first_name)
        assert len(results) >= 1
        assert any(c.id == test_contact.id for c in results)
        
        # Filter by company
        contacts_list, total_count = repo.filter_by(filters={'company': test_contact.company})
        assert len(contacts_list) >= 1
        assert total_count >= 1


class TestUserRepository:
    """Tests for UserRepository"""
    
    def test_create_user(self, db: Session):
        """Test creating a user"""
        repo = UserRepository(db)
        
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'hashed_password': 'hashed123',
            'is_active': True
        }
        
        user = repo.create_user(user_data)
        repo.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
    
    def test_get_user_by_username(self, db: Session):
        """Test getting user by username"""
        repo = UserRepository(db)
        
        # Create user
        user = repo.create_user({
            'username': 'findme',
            'email': 'findme@example.com',
            'hashed_password': 'hash',
            'is_active': True
        })
        repo.commit()
        
        # Find user
        found = repo.get_user_by_username('findme')
        assert found is not None
        assert found.username == 'findme'
    
    def test_get_user_by_email(self, db: Session):
        """Test getting user by email"""
        repo = UserRepository(db)
        
        user = repo.create_user({
            'username': 'emailuser',
            'email': 'unique@example.com',
            'hashed_password': 'hash',
            'is_active': True
        })
        repo.commit()
        
        found = repo.get_user_by_email('unique@example.com')
        assert found is not None
        assert found.email == 'unique@example.com'
    
    def test_get_active_users(self, db: Session):
        """Test getting active users"""
        repo = UserRepository(db)
        
        active_users = repo.get_active_users()
        assert isinstance(active_users, list)


class TestOCRRepository:
    """Tests for OCRRepository"""
    
    def test_create_training_data(self, db: Session, test_contact: Contact):
        """Test creating OCR correction data"""
        repo = OCRRepository(db)
        
        correction_data = {
            'contact_id': test_contact.id,
            'original_text': 'John Doe',
            'original_box': '{"x": 10, "y": 20, "width": 100, "height": 30}',
            'corrected_text': 'John Doe',
            'corrected_field': 'full_name'
        }
        
        ocr_data = repo.create_training_data(correction_data)
        repo.commit()
        
        assert ocr_data.id is not None
        assert ocr_data.original_text == 'John Doe'
    
    def test_get_training_data_by_contact(self, db: Session, test_contact: Contact):
        """Test getting OCR corrections by contact"""
        repo = OCRRepository(db)
        
        # Create correction data
        repo.create_training_data({
            'contact_id': test_contact.id,
            'original_text': 'Test',
            'original_box': '{"x": 0, "y": 0, "width": 50, "height": 20}',
            'corrected_text': 'Test',
            'corrected_field': 'first_name'
        })
        repo.commit()
        
        data = repo.get_training_data_by_contact(test_contact.id)
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_mark_as_validated(self, db: Session, test_contact: Contact):
        """Test updating OCR correction"""
        repo = OCRRepository(db)
        
        correction = repo.create_training_data({
            'contact_id': test_contact.id,
            'original_text': 'Test',
            'original_box': '{"x": 5, "y": 5, "width": 80, "height": 25}',
            'corrected_text': 'Test Corrected',
            'corrected_field': 'first_name'
        })
        repo.commit()
        
        # Update using update_training_data method
        updated = repo.update_training_data(correction, {'corrected_text': 'Final Text'})
        repo.commit()
        
        assert updated.corrected_text == 'Final Text'


class TestSettingsRepository:
    """Tests for SettingsRepository"""
    
    def test_create_setting(self, db: Session):
        """Test creating an app setting"""
        repo = SettingsRepository(db)
        
        setting_data = {
            'key': 'test_setting',
            'value': 'test_value'
        }
        setting = repo.create_setting(setting_data)
        repo.commit()
        
        assert setting.key == 'test_setting'
        assert setting.value == 'test_value'
    
    def test_get_setting_by_key(self, db: Session):
        """Test getting setting by key"""
        repo = SettingsRepository(db)
        
        # Create setting
        repo.create_setting({'key': 'find_me_key', 'value': 'find_me_value'})
        repo.commit()
        
        # Find setting
        found = repo.get_setting_by_key('find_me_key')
        assert found is not None
        assert found.value == 'find_me_value'
    
    def test_update_setting_value(self, db: Session):
        """Test updating setting value"""
        repo = SettingsRepository(db)
        
        # Create setting
        repo.create_setting({'key': 'update_me', 'value': 'old_value'})
        repo.commit()
        
        # Update setting
        updated = repo.update_setting_value('update_me', 'new_value')
        repo.commit()
        
        assert updated is not None
        assert updated.value == 'new_value'


class TestAuditRepository:
    """Tests for AuditRepository"""
    
    def test_create_audit_log(self, db: Session, test_contact: Contact):
        """Test creating an audit log"""
        repo = AuditRepository(db)
        
        # Create test user first
        user = User(
            username='audit_user',
            email='audit@example.com',
            hashed_password='hash',
            is_active=True
        )
        db.add(user)
        db.commit()
        
        audit_data = {
            'user_id': user.id,
            'username': 'audit_user',
            'action': 'created',
            'entity_type': 'contact',
            'contact_id': test_contact.id,
            'changes': '{"field": "name", "old": "", "new": "Test"}'
        }
        
        audit = repo.create_audit_log(audit_data)
        repo.commit()
        
        assert audit.id is not None
        assert audit.action == 'created'
    
    def test_get_audit_logs_by_user(self, db: Session, test_contact: Contact):
        """Test getting audit logs by user"""
        repo = AuditRepository(db)
        
        # Create user and audit log
        user = User(
            username='log_user',
            email='log@example.com',
            hashed_password='hash',
            is_active=True
        )
        db.add(user)
        db.commit()
        
        repo.create_audit_log({
            'user_id': user.id,
            'username': 'log_user',
            'action': 'updated',
            'entity_type': 'contact',
            'contact_id': test_contact.id
        })
        repo.commit()
        
        logs = repo.get_audit_logs_by_user(user.id)
        assert isinstance(logs, list)
        assert len(logs) >= 1
    
    def test_get_audit_logs_by_action(self, db: Session):
        """Test getting audit logs by action"""
        repo = AuditRepository(db)
        
        logs = repo.get_audit_logs_by_action('create')
        assert isinstance(logs, list)

