"""
Tests for Service Layer
"""

import pytest
from sqlalchemy.orm import Session

from ..models import Contact
from ..services import ContactService


class TestContactService:
    """Tests for ContactService"""
    
    @pytest.fixture
    def contact_service(self, test_db: Session):
        """Create ContactService instance"""
        return ContactService(test_db)
    
    def test_get_contacts_list(self, contact_service, test_contact):
        """Test getting paginated contacts list"""
        contacts, total = contact_service.get_contacts_list(skip=0, limit=10)
        
        assert isinstance(contacts, list)
        assert isinstance(total, int)
        assert total >= 1
        assert len(contacts) <= 10
    
    def test_get_contacts_with_filters(self, contact_service, test_contact):
        """Test getting contacts with filters"""
        contacts, total = contact_service.get_contacts_list(
            q=test_contact.first_name,
            skip=0,
            limit=10
        )
        
        assert isinstance(contacts, list)
        assert any(c.first_name == test_contact.first_name for c in contacts)
    
    def test_get_contacts_with_company_filter(self, contact_service, test_contact):
        """Test filtering by company"""
        contacts, total = contact_service.get_contacts_list(
            company=test_contact.company,
            skip=0,
            limit=10
        )
        
        assert isinstance(contacts, list)
        if contacts:
            assert all(c.company == test_contact.company for c in contacts)
    
    def test_get_contacts_with_sorting(self, contact_service):
        """Test sorting contacts"""
        contacts, _ = contact_service.get_contacts_list(
            sort_by="first_name",
            sort_order="asc",
            skip=0,
            limit=10
        )
        
        assert isinstance(contacts, list)
        # Verify sorting (if more than 1 contact)
        if len(contacts) > 1:
            names = [c.first_name for c in contacts if c.first_name]
            assert names == sorted(names)
    
    def test_create_contact(self, contact_service):
        """Test creating a contact via service"""
        contact_data = {
            'uid': 'service-test-123',
            'first_name': 'Service',
            'last_name': 'Test',
            'email': 'service@test.com',
            'company': 'Test Service Co'
        }
        
        contact = contact_service.create_contact(contact_data)
        
        assert contact.id is not None
        assert contact.first_name == 'Service'
        assert contact.email == 'service@test.com'
    
    def test_get_contact_by_id(self, contact_service, test_contact):
        """Test getting contact by ID via service"""
        contact = contact_service.get_contact_by_id(test_contact.id)
        
        assert contact is not None
        assert contact.id == test_contact.id
        assert contact.first_name == test_contact.first_name
    
    def test_get_nonexistent_contact(self, contact_service):
        """Test getting non-existent contact"""
        contact = contact_service.get_contact_by_id(99999)
        
        assert contact is None
    
    def test_update_contact(self, contact_service, test_contact):
        """Test updating contact via service"""
        update_data = {
            'first_name': 'Updated Service'
        }
        
        updated = contact_service.update_contact(test_contact.id, update_data)
        
        assert updated is not None
        assert updated.first_name == 'Updated Service'
    
    def test_delete_contact(self, contact_service, test_contact):
        """Test deleting contact via service"""
        contact_id = test_contact.id
        
        result = contact_service.delete_contact(contact_id)
        
        assert result is True
        
        # Verify deletion
        deleted = contact_service.get_contact_by_id(contact_id)
        assert deleted is None
    
    def test_search_contacts(self, contact_service, test_contact):
        """Test searching contacts"""
        results = contact_service.search_contacts(test_contact.first_name)
        
        assert isinstance(results, list)
        assert any(c.id == test_contact.id for c in results)
    
    def test_get_contacts_by_company(self, contact_service, test_contact):
        """Test getting contacts by company"""
        contacts = contact_service.get_contacts_by_company(test_contact.company)
        
        assert isinstance(contacts, list)
        assert all(c.company == test_contact.company for c in contacts)
    
    def test_count_contacts(self, contact_service):
        """Test counting total contacts"""
        count = contact_service.count_contacts()
        
        assert isinstance(count, int)
        assert count >= 0
    
    def test_bulk_update_contacts(self, contact_service, test_db):
        """Test bulk updating contacts"""
        # Create test contacts
        import uuid
        contacts = []
        for i in range(3):
            contact = Contact(
                uid=f'bulk-{uuid.uuid4()}',
                first_name=f'Bulk{i}',
                company='Old Company'
            )
            test_db.add(contact)
            contacts.append(contact)
        test_db.commit()
        
        contact_ids = [c.id for c in contacts]
        update_data = {'company': 'New Company'}
        
        result = contact_service.bulk_update_contacts(contact_ids, update_data)
        
        assert result is True
        
        # Verify updates
        for contact_id in contact_ids:
            updated = contact_service.get_contact_by_id(contact_id)
            assert updated.company == 'New Company'
    
    def test_bulk_delete_contacts(self, contact_service, test_db):
        """Test bulk deleting contacts"""
        # Create test contacts
        import uuid
        contacts = []
        for i in range(3):
            contact = Contact(
                uid=f'bulk-del-{uuid.uuid4()}',
                first_name=f'BulkDel{i}'
            )
            test_db.add(contact)
            contacts.append(contact)
        test_db.commit()
        
        contact_ids = [c.id for c in contacts]
        
        result = contact_service.bulk_delete_contacts(contact_ids)
        
        assert result is True
        
        # Verify deletion
        for contact_id in contact_ids:
            deleted = contact_service.get_contact_by_id(contact_id)
            assert deleted is None


class TestContactServiceValidation:
    """Tests for ContactService validation"""
    
    @pytest.fixture
    def contact_service(self, test_db: Session):
        """Create ContactService instance"""
        return ContactService(test_db)
    
    def test_create_contact_with_duplicate_email(self, contact_service, test_contact):
        """Test creating contact with duplicate email"""
        contact_data = {
            'uid': 'duplicate-test',
            'first_name': 'Duplicate',
            'email': test_contact.email  # Duplicate email
        }
        
        # Should either raise error or handle gracefully
        # Implementation depends on business logic
        try:
            contact = contact_service.create_contact(contact_data)
            # If no error, verify it was created
            assert contact is not None
        except Exception as e:
            # If error, verify it's appropriate
            assert "duplicate" in str(e).lower() or "exists" in str(e).lower()
    
    def test_update_nonexistent_contact(self, contact_service):
        """Test updating non-existent contact"""
        result = contact_service.update_contact(99999, {'first_name': 'Test'})
        
        assert result is None
    
    def test_delete_nonexistent_contact(self, contact_service):
        """Test deleting non-existent contact"""
        result = contact_service.delete_contact(99999)
        
        assert result is False


class TestContactServicePerformance:
    """Tests for ContactService performance"""
    
    @pytest.fixture
    def contact_service(self, test_db: Session):
        """Create ContactService instance"""
        return ContactService(test_db)
    
    def test_get_contacts_list_performance(self, contact_service):
        """Test performance of getting contacts list"""
        import time
        
        start = time.time()
        contacts, total = contact_service.get_contacts_list(skip=0, limit=100)
        duration = time.time() - start
        
        # Should complete in reasonable time (<1 second for small dataset)
        assert duration < 1.0
        assert isinstance(contacts, list)
    
    def test_search_performance(self, contact_service):
        """Test search performance"""
        import time
        
        start = time.time()
        results = contact_service.search_contacts("test")
        duration = time.time() - start
        
        # Search should be fast
        assert duration < 1.0
        assert isinstance(results, list)
