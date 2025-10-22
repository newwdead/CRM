"""
Tests for Repository Layer
Testing all repositories (Contact, Duplicate, User, OCR, Settings, Audit)
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import Contact, DuplicateContact, User, OCRCorrection, AppSetting, AuditLog
from ..repositories import (
    ContactRepository,
    DuplicateRepository,
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
        
        contact = repo.create_contact(contact_data)
        repo.commit()
        
        assert contact.id is not None
        assert contact.first_name == 'John'
        assert contact.email == 'john@example.com'
    
    def test_get_contact_by_id(self, db: Session, test_contact: Contact):
        """Test getting contact by ID"""
        repo = ContactRepository(db)
        
        found = repo.get_contact_by_id(test_contact.id)
        
        assert found is not None
        assert found.id == test_contact.id
        assert found.first_name == test_contact.first_name
    
    def test_get_contact_by_uid(self, db: Session, test_contact: Contact):
        """Test getting contact by UID"""
        repo = ContactRepository(db)
        
        found = repo.get_contact_by_uid(test_contact.uid)
        
        assert found is not None
        assert found.uid == test_contact.uid
    
    def test_update_contact(self, db: Session, test_contact: Contact):
        """Test updating a contact"""
        repo = ContactRepository(db)
        
        updated = repo.update_contact(test_contact, {'first_name': 'Jane'})
        repo.commit()
        
        assert updated.first_name == 'Jane'
    
    def test_delete_contact(self, db: Session, test_contact: Contact):
        """Test deleting a contact"""
        repo = ContactRepository(db)
        
        contact_id = test_contact.id
        repo.delete_contact(test_contact)
        repo.commit()
        
        found = repo.get_contact_by_id(contact_id)
        assert found is None
    
    def test_count_contacts(self, db: Session, test_contact: Contact):
        """Test counting contacts"""
        repo = ContactRepository(db)
        
        count = repo.count_contacts()
        assert count >= 1
    
    def test_search_and_filter_contacts(self, db: Session, test_contact: Contact):
        """Test search and filter"""
        repo = ContactRepository(db)
        
        # Search by name
        results = repo.search_and_filter_contacts(q=test_contact.first_name)
        assert len(results) >= 1
        assert any(c.id == test_contact.id for c in results)
        
        # Filter by company
        results = repo.search_and_filter_contacts(company=test_contact.company)
        assert len(results) >= 1


class TestDuplicateRepository:
    """Tests for DuplicateRepository"""
    
    def test_create_duplicate(self, db: Session, test_contact: Contact):
        """Test creating a duplicate record"""
        repo = DuplicateRepository(db)
        
        # Create second contact
        contact2 = Contact(
            uid='test-uid-2',
            first_name='John',
            last_name='Doe',
            email='john2@example.com'
        )
        db.add(contact2)
        db.commit()
        
        duplicate_data = {
            'contact_id_1': test_contact.id,
            'contact_id_2': contact2.id,
            'similarity': 0.85,
            'match_type': 'name'
        }
        
        duplicate = repo.create_duplicate(duplicate_data)
        repo.commit()
        
        assert duplicate.id is not None
        assert duplicate.similarity == 0.85
    
    def test_get_duplicates_for_contact(self, db: Session, test_contact: Contact):
        """Test getting duplicates for a contact"""
        repo = DuplicateRepository(db)
        
        duplicates = repo.get_duplicates_for_contact(test_contact.id)
        assert isinstance(duplicates, list)
    
    def test_get_pending_duplicates(self, db: Session):
        """Test getting pending duplicates"""
        repo = DuplicateRepository(db)
        
        pending = repo.get_pending_duplicates()
        assert isinstance(pending, list)
    
    def test_mark_as_resolved(self, db: Session, test_contact: Contact):
        """Test marking duplicate as resolved"""
        repo = DuplicateRepository(db)
        
        # Create duplicate first
        contact2 = Contact(uid='test-uid-3', first_name='Test')
        db.add(contact2)
        db.commit()
        
        dup = repo.create_duplicate({
            'contact_id_1': test_contact.id,
            'contact_id_2': contact2.id,
            'similarity': 0.9
        })
        repo.commit()
        
        # Mark as resolved
        resolved = repo.mark_as_resolved(dup.id)
        repo.commit()
        
        assert resolved.resolved is True


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
        """Test creating OCR training data"""
        repo = OCRRepository(db)
        
        training_data = {
            'contact_id': test_contact.id,
            'original_text': 'John Doe',
            'corrected_text': 'John Doe',
            'field_name': 'full_name',
            'validated': False
        }
        
        ocr_data = repo.create_training_data(training_data)
        repo.commit()
        
        assert ocr_data.id is not None
        assert ocr_data.original_text == 'John Doe'
    
    def test_get_training_data_by_contact(self, db: Session, test_contact: Contact):
        """Test getting training data by contact"""
        repo = OCRRepository(db)
        
        # Create training data
        repo.create_training_data({
            'contact_id': test_contact.id,
            'original_text': 'Test',
            'corrected_text': 'Test',
            'field_name': 'name',
            'validated': False
        })
        repo.commit()
        
        data = repo.get_training_data_by_contact(test_contact.id)
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_mark_as_validated(self, db: Session, test_contact: Contact):
        """Test marking training data as validated"""
        repo = OCRRepository(db)
        
        training = repo.create_training_data({
            'contact_id': test_contact.id,
            'original_text': 'Test',
            'corrected_text': 'Test',
            'field_name': 'name',
            'validated': False
        })
        repo.commit()
        
        validated = repo.mark_as_validated(training.id)
        repo.commit()
        
        assert validated.validated is True


class TestSettingsRepository:
    """Tests for SettingsRepository"""
    
    def test_create_setting(self, db: Session):
        """Test creating a setting"""
        repo = SettingsRepository(db)
        
        setting_data = {
            'key': 'test_setting',
            'value': 'test_value',
            'category': 'general'
        }
        
        setting = repo.create_setting(setting_data)
        repo.commit()
        
        assert setting.id is not None
        assert setting.key == 'test_setting'
    
    def test_get_setting_by_key(self, db: Session):
        """Test getting setting by key"""
        repo = SettingsRepository(db)
        
        # Create setting
        repo.create_setting({
            'key': 'find_me_key',
            'value': 'find_me_value',
            'category': 'test'
        })
        repo.commit()
        
        # Find setting
        found = repo.get_setting_by_key('find_me_key')
        assert found is not None
        assert found.value == 'find_me_value'
    
    def test_update_setting_value(self, db: Session):
        """Test updating setting value"""
        repo = SettingsRepository(db)
        
        setting = repo.create_setting({
            'key': 'update_me',
            'value': 'old_value',
            'category': 'test'
        })
        repo.commit()
        
        updated = repo.update_setting_value('update_me', 'new_value')
        repo.commit()
        
        assert updated.value == 'new_value'


class TestAuditRepository:
    """Tests for AuditRepository"""
    
    def test_create_audit_log(self, db: Session):
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
            'action': 'create',
            'entity_type': 'contact',
            'entity_id': 1,
            'details': 'Test audit log'
        }
        
        audit = repo.create_audit_log(audit_data)
        repo.commit()
        
        assert audit.id is not None
        assert audit.action == 'create'
    
    def test_get_audit_logs_by_user(self, db: Session):
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
            'action': 'update',
            'entity_type': 'contact',
            'entity_id': 1
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

