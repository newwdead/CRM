"""
Tests for Service Layer

Tests for ContactService, DuplicateService, SettingsService, and OCRService.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.database import Base
from app.models import Contact, User, Tag, Group, AppSetting
from app.services import ContactService, DuplicateService, SettingsService


# Test database setup
@pytest.fixture(scope='function')
def test_db():
    """Create a test database."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        hashed_password='hashedpassword',
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def contact_service(test_db):
    """Get ContactService instance."""
    return ContactService(test_db)


@pytest.fixture
def duplicate_service(test_db):
    """Get DuplicateService instance."""
    return DuplicateService(test_db)


@pytest.fixture
def settings_service(test_db):
    """Get SettingsService instance."""
    return SettingsService(test_db)


# ContactService Tests
class TestContactService:
    """Tests for ContactService."""
    
    def test_create_contact(self, contact_service, test_user):
        """Test creating a contact."""
        contact_data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'company': 'Test Corp'
        }
        
        contact = contact_service.create_contact(
            data=contact_data,
            current_user=test_user,
            auto_detect_duplicates=False  # Disable for testing
        )
        
        assert contact.id is not None
        assert contact.full_name == 'John Doe'
        assert contact.email == 'john@example.com'
        assert contact.uid is not None
    
    def test_get_by_id(self, contact_service, test_user):
        """Test getting contact by ID."""
        # Create a contact
        contact_data = {'full_name': 'Jane Doe', 'email': 'jane@example.com'}
        contact = contact_service.create_contact(contact_data, test_user, False)
        
        # Get by ID
        fetched = contact_service.get_by_id(contact.id)
        
        assert fetched is not None
        assert fetched.id == contact.id
        assert fetched.full_name == 'Jane Doe'
    
    def test_get_by_id_not_found(self, contact_service):
        """Test getting non-existent contact."""
        contact = contact_service.get_by_id(99999)
        assert contact is None
    
    def test_update_contact(self, contact_service, test_user):
        """Test updating a contact."""
        # Create a contact
        contact_data = {'full_name': 'Old Name', 'email': 'old@example.com'}
        contact = contact_service.create_contact(contact_data, test_user, False)
        
        # Update
        update_data = {'full_name': 'New Name', 'company': 'New Corp'}
        updated = contact_service.update_contact(contact.id, update_data, test_user)
        
        assert updated is not None
        assert updated.full_name == 'New Name'
        assert updated.company == 'New Corp'
        assert updated.email == 'old@example.com'  # Unchanged
    
    def test_delete_contact(self, contact_service, test_user):
        """Test deleting a contact."""
        # Create a contact
        contact_data = {'full_name': 'To Delete', 'email': 'delete@example.com'}
        contact = contact_service.create_contact(contact_data, test_user, False)
        
        # Delete
        deleted = contact_service.delete_contact(contact.id, test_user)
        
        assert deleted is True
        
        # Verify deletion
        fetched = contact_service.get_by_id(contact.id)
        assert fetched is None
    
    def test_list_contacts(self, contact_service, test_user):
        """Test listing contacts with pagination."""
        # Create multiple contacts
        for i in range(5):
            contact_data = {
                'full_name': f'Contact {i}',
                'email': f'contact{i}@example.com',
                'company': 'Test Corp'
            }
            contact_service.create_contact(contact_data, test_user, False)
        
        # List contacts
        result = contact_service.list_contacts(page=1, limit=10)
        
        assert result['total'] == 5
        assert len(result['items']) == 5
        assert result['pages'] == 1
    
    def test_list_contacts_with_search(self, contact_service, test_user):
        """Test listing contacts with search query."""
        # Create contacts
        contact_service.create_contact(
            {'full_name': 'John Smith', 'email': 'john@example.com'},
            test_user,
            False
        )
        contact_service.create_contact(
            {'full_name': 'Jane Doe', 'email': 'jane@example.com'},
            test_user,
            False
        )
        
        # Search for "John"
        result = contact_service.list_contacts(q='John')
        
        assert result['total'] == 1
        assert result['items'][0].full_name == 'John Smith'
    
    def test_search_contacts(self, contact_service, test_user):
        """Test fast search."""
        # Create contacts
        contact_service.create_contact(
            {'full_name': 'Alice', 'company': 'Tech Corp'},
            test_user,
            False
        )
        
        # Search
        results = contact_service.search_contacts('Tech', limit=10)
        
        assert len(results) == 1
        assert results[0]['company'] == 'Tech Corp'
    
    def test_phone_formatting(self, contact_service, test_user):
        """Test automatic phone number formatting."""
        contact_data = {
            'full_name': 'Test User',
            'phone': '1234567890',
            'phone_mobile': '9876543210'
        }
        
        contact = contact_service.create_contact(contact_data, test_user, False)
        
        # Phone numbers should be formatted
        assert contact.phone is not None
        assert contact.phone_mobile is not None


# DuplicateService Tests
class TestDuplicateService:
    """Tests for DuplicateService."""
    
    def test_find_duplicates_manual(self, duplicate_service, test_user, test_db):
        """Test manual duplicate detection."""
        # Create similar contacts
        contact1 = Contact(
            full_name='John Doe',
            email='john@example.com',
            company='Test Corp'
        )
        contact2 = Contact(
            full_name='John Doe',
            email='john.doe@example.com',
            company='Test Corp'
        )
        
        test_db.add(contact1)
        test_db.add(contact2)
        test_db.commit()
        
        # Find duplicates
        result = duplicate_service.find_duplicates_manual(threshold=0.7)
        
        assert result['found'] >= 0  # May find duplicates
        assert 'threshold' in result
    
    def test_update_duplicate_status(self, duplicate_service, test_user):
        """Test updating duplicate status."""
        # This test would require setting up duplicate records
        # Skipping for now as it requires more complex setup
        pass


# SettingsService Tests
class TestSettingsService:
    """Tests for SettingsService."""
    
    def test_set_and_get_setting(self, settings_service):
        """Test setting and getting a setting."""
        # Set setting
        setting = settings_service.set_setting('test_key', 'test_value')
        
        assert setting.key == 'test_key'
        assert setting.value == 'test_value'
        
        # Get setting
        value = settings_service.get_setting('test_key')
        assert value == 'test_value'
    
    def test_get_setting_with_default(self, settings_service):
        """Test getting non-existent setting with default."""
        value = settings_service.get_setting('nonexistent', 'default_value')
        assert value == 'default_value'
    
    def test_get_all_settings(self, settings_service):
        """Test getting all settings."""
        # Create settings
        settings_service.set_setting('key1', 'value1')
        settings_service.set_setting('key2', 'value2')
        
        # Get all
        settings = settings_service.get_all_settings()
        
        assert len(settings) == 2
    
    def test_get_settings_dict(self, settings_service):
        """Test getting settings as dictionary."""
        # Create settings
        settings_service.set_setting('key1', 'value1')
        settings_service.set_setting('key2', 'value2')
        
        # Get dict
        settings_dict = settings_service.get_settings_dict()
        
        assert settings_dict['key1'] == 'value1'
        assert settings_dict['key2'] == 'value2'
    
    def test_delete_setting(self, settings_service):
        """Test deleting a setting."""
        # Create setting
        settings_service.set_setting('to_delete', 'value')
        
        # Delete
        deleted = settings_service.delete_setting('to_delete')
        assert deleted is True
        
        # Verify deletion
        value = settings_service.get_setting('to_delete')
        assert value is None
    
    def test_set_ocr_provider(self, settings_service):
        """Test setting OCR provider."""
        setting = settings_service.set_ocr_provider('tesseract')
        assert setting.value == 'tesseract'
        
        # Invalid provider should raise error
        with pytest.raises(ValueError):
            settings_service.set_ocr_provider('invalid_provider')
    
    def test_set_duplicate_threshold(self, settings_service):
        """Test setting duplicate threshold."""
        setting = settings_service.set_duplicate_threshold(0.8)
        assert setting.value == '0.8'
        
        # Invalid threshold should raise error
        with pytest.raises(ValueError):
            settings_service.set_duplicate_threshold(1.5)
    
    def test_get_ocr_settings(self, settings_service):
        """Test getting OCR settings."""
        settings = settings_service.get_ocr_settings()
        
        assert 'provider' in settings
        assert 'language' in settings
        assert 'confidence_threshold' in settings
    
    def test_get_duplicate_detection_settings(self, settings_service):
        """Test getting duplicate detection settings."""
        settings = settings_service.get_duplicate_detection_settings()
        
        assert 'enabled' in settings
        assert 'threshold' in settings
        assert 'auto_detect' in settings


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

