"""
Unit tests for duplicate detection utilities
"""
import pytest
from ..duplicate_utils import (
    calculate_field_similarity,
    calculate_contact_similarity,
    find_duplicate_contacts,
    find_duplicates_for_new_contact,
    merge_contacts,
    get_mergeable_fields
)


class TestFieldSimilarity:
    """Test field similarity calculation"""
    
    def test_exact_match(self):
        """Test exact field match returns 1.0"""
        assert calculate_field_similarity("test@example.com", "test@example.com") == 1.0
    
    def test_different_case(self):
        """Test case-insensitive comparison"""
        assert calculate_field_similarity("Test", "test") > 0.9
    
    def test_empty_fields(self):
        """Test empty fields return 0"""
        assert calculate_field_similarity("", "") == 0
        assert calculate_field_similarity("test", "") == 0
        assert calculate_field_similarity("", "test") == 0
    
    def test_similar_names(self):
        """Test similar but not exact names"""
        score = calculate_field_similarity("John Smith", "Jon Smith")
        assert 0.7 < score < 1.0
    
    def test_phone_normalization(self):
        """Test phone number normalization"""
        score = calculate_field_similarity("+7 (900) 123-45-67", "79001234567", field_type='phone')
        assert score == 1.0


class TestContactSimilarity:
    """Test contact similarity calculation"""
    
    def test_identical_contacts(self):
        """Test identical contacts return score ~1.0"""
        contact1 = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '79001234567',
            'company': 'Test Corp',
            'position': 'Manager'
        }
        contact2 = contact1.copy()
        
        score, fields = calculate_contact_similarity(contact1, contact2)
        assert score > 0.9
    
    def test_completely_different(self):
        """Test completely different contacts"""
        contact1 = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '79001234567',
            'company': 'Test Corp'
        }
        contact2 = {
            'full_name': 'Jane Smith',
            'email': 'jane@other.com',
            'phone': '79009999999',
            'company': 'Other Corp'
        }
        
        score, fields = calculate_contact_similarity(contact1, contact2)
        # Different contacts should have low similarity (< 0.5)
        assert score < 0.5
    
    def test_partial_match(self):
        """Test contacts with some matching fields"""
        contact1 = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'company': 'Test Corp'
        }
        contact2 = {
            'full_name': 'John Doe',
            'email': 'john.doe@example.com',  # Different but similar
            'company': 'Test Corp'
        }
        
        score, fields = calculate_contact_similarity(contact1, contact2)
        assert 0.5 < score < 0.9


class TestFindDuplicates:
    """Test duplicate finding functionality"""
    
    def test_find_duplicates_in_list(self):
        """Test finding duplicates in a contact list"""
        contacts = [
            {
                'id': 1,
                'full_name': 'John Doe',
                'email': 'john@example.com',
                'phone': '79001234567'
            },
            {
                'id': 2,
                'full_name': 'John Doe',
                'email': 'john@example.com',
                'phone': '79001234567'
            },
            {
                'id': 3,
                'full_name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '79009999999'
            }
        ]
        
        duplicates = find_duplicate_contacts(contacts, threshold=0.8)
        assert len(duplicates) >= 1  # Should find at least one duplicate pair
    
    def test_no_duplicates(self):
        """Test when no duplicates exist"""
        contacts = [
            {'id': 1, 'full_name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'full_name': 'Jane Smith', 'email': 'jane@example.com'},
            {'id': 3, 'full_name': 'Bob Johnson', 'email': 'bob@example.com'}
        ]
        
        duplicates = find_duplicate_contacts(contacts, threshold=0.9)
        assert len(duplicates) == 0
    
    def test_threshold_filtering(self):
        """Test that threshold properly filters results"""
        contacts = [
            {'id': 1, 'full_name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'full_name': 'Jon Doe', 'email': 'jon@example.com'}  # Similar but not identical
        ]
        
        # High threshold - might not find duplicates
        high_threshold_dupes = find_duplicate_contacts(contacts, threshold=0.99)
        # Low threshold - should find duplicates
        low_threshold_dupes = find_duplicate_contacts(contacts, threshold=0.5)
        
        assert len(low_threshold_dupes) >= len(high_threshold_dupes)


class TestMergeContacts:
    """Test contact merging functionality"""
    
    def test_merge_keep_primary(self):
        """Test merging with primary field selection"""
        contact1 = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone': '79001234567'
        }
        contact2 = {
            'full_name': 'John D.',
            'email': 'j.doe@example.com',
            'phone': '79007654321'
        }
        
        selected_fields = {
            'full_name': 'primary',
            'email': 'primary',
            'phone': 'secondary'
        }
        
        merged = merge_contacts(contact1, contact2, selected_fields)
        assert merged['full_name'] == 'John Doe'
        assert merged['email'] == 'john@example.com'
        assert merged['phone'] == '79007654321'
    
    def test_merge_combine_fields(self):
        """Test combining fields from both contacts"""
        contact1 = {
            'phone': '79001234567',
            'phone_mobile': None
        }
        contact2 = {
            'phone': None,
            'phone_mobile': '79009999999'
        }
        
        selected_fields = {
            'phone': 'primary',
            'phone_mobile': 'secondary'
        }
        
        merged = merge_contacts(contact1, contact2, selected_fields)
        assert merged['phone'] == '79001234567'
        assert merged['phone_mobile'] == '79009999999'


class TestMergeableFields:
    """Test get_mergeable_fields function"""
    
    def test_returns_field_list(self):
        """Test that function returns list of field names"""
        fields = get_mergeable_fields()
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert 'full_name' in fields
        assert 'email' in fields
        assert 'phone' in fields

