"""
Tests for Contacts API Endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestContactsAPI:
    """Tests for /contacts endpoints"""
    
    def test_list_contacts_unauthorized(self, client):
        """Test listing contacts without authentication"""
        response = client.get("/contacts/")
        assert response.status_code in [401, 307]  # Unauthorized or redirect
    
    def test_list_contacts_authorized(self, client, auth_token):
        """Test listing contacts with authentication"""
        response = client.get(
            "/contacts/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    def test_list_contacts_pagination(self, client, auth_token):
        """Test contacts list pagination"""
        response = client.get(
            "/contacts/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
    
    def test_list_contacts_search(self, client, auth_token, test_contact):
        """Test contacts search"""
        response = client.get(
            f"/contacts/?q={test_contact.first_name}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_get_contact_by_id(self, client, auth_token, test_contact):
        """Test getting specific contact by ID"""
        response = client.get(
            f"/contacts/{test_contact.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_contact.id
        assert data["first_name"] == test_contact.first_name
    
    def test_get_nonexistent_contact(self, client, auth_token):
        """Test getting non-existent contact"""
        response = client.get(
            "/contacts/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
    
    def test_create_contact(self, client, auth_token):
        """Test creating a new contact"""
        contact_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "company": "Test Co"
        }
        response = client.post(
            "/contacts/",
            json=contact_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        print(f"DEBUG: Response data: {data}")
        print(f"DEBUG: Data type: {type(data)}")
        print(f"DEBUG: Data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        # API might return {success: true, contact: {...}} or just {...}
        if isinstance(data, dict) and "contact" in data:
            contact = data["contact"]
        elif isinstance(data, dict) and "data" in data:
            contact = data["data"]
        else:
            contact = data
        
        assert contact.get("first_name") == "Test"
        assert contact.get("email") == "test@example.com"
    
    def test_create_contact_invalid_data(self, client, auth_token):
        """Test creating contact with invalid data"""
        contact_data = {
            "first_name": "",  # Invalid: empty name
            "email": "invalid-email"  # Invalid email format
        }
        response = client.post(
            "/contacts",
            json=contact_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_update_contact(self, client, auth_token, test_contact):
        """Test updating a contact"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = client.put(
            f"/contacts/{test_contact.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
    
    def test_delete_contact(self, client, auth_token, test_contact):
        """Test deleting a contact"""
        response = client.delete(
            f"/contacts/{test_contact.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code in [200, 204]
        
        # Verify deletion
        get_response = client.get(
            f"/contacts/{test_contact.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404
    
    def test_bulk_delete_contacts(self, client, auth_token, test_db):
        """Test bulk deleting contacts"""
        from ..models import Contact
        import uuid
        
        # Create test contacts
        contact_ids = []
        for i in range(3):
            contact = Contact(
                uid=f'bulk-test-{uuid.uuid4()}',
                first_name=f'Bulk{i}',
                last_name='Test'
            )
            test_db.add(contact)
            test_db.commit()
            test_db.refresh(contact)
            contact_ids.append(contact.id)
        
        response = client.post(
            "/contacts/bulk-delete",
            json={"ids": contact_ids},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_contact_filters(self, client, auth_token, test_contact):
        """Test contact filtering"""
        # Filter by company
        response = client.get(
            f"/contacts?company={test_contact.company}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        # Filter by position
        if test_contact.position:
            response = client.get(
                f"/contacts?position={test_contact.position}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
    
    def test_contact_sorting(self, client, auth_token):
        """Test contact sorting"""
        response = client.get(
            "/contacts?sort_by=first_name&sort_order=asc",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestContactsExport:
    """Tests for contact export endpoints"""
    
    def test_export_contacts_csv(self, client, auth_token):
        """Test exporting contacts to CSV"""
        response = client.get(
            "/contacts/export/csv",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
    
    def test_export_contacts_excel(self, client, auth_token):
        """Test exporting contacts to Excel"""
        response = client.get(
            "/contacts/export/excel",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
    
    def test_export_contacts_vcard(self, client, auth_token):
        """Test exporting contacts to vCard"""
        response = client.get(
            "/contacts/export/vcard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200


class TestContactStats:
    """Tests for contact statistics endpoints"""
    
    def test_get_contacts_stats(self, client, auth_token):
        """Test getting contact statistics"""
        response = client.get(
            "/contacts/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)

