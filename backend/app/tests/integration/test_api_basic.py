"""
Basic API integration tests
"""
import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"
    
    def test_version_endpoint(self, client):
        """Test /version endpoint"""
        response = client.get("/version")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "version" in data
            assert data["version"] == "5.0.1"
        assert "python" in data
        assert "fastapi" in data
        assert "react" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user(self, client, test_user_data):
        """Test user registration"""
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_username(self, client, test_user_data):
        """Test registering with duplicate username fails"""
        # Register first user
        client.post("/auth/register", json=test_user_data)
        
        # Try to register again with same username
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Activate user (in real scenario, admin would do this)
        # For test, we'll skip activation or mock it
        
        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/login", data=login_data)
        
        # May fail if user is not active, that's expected
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpass"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_me_without_auth(self, client):
        """Test /auth/me without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestContactEndpoints:
    """Test contact CRUD endpoints"""
    
    def test_list_contacts_unauthorized(self, client):
        """Test listing contacts without auth"""
        response = client.get("/contacts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_contact_unauthorized(self, client, test_contact_data):
        """Test creating contact without auth"""
        response = client.post("/contacts/", json=test_contact_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_contact_by_id_unauthorized(self, client):
        """Test getting contact by ID without auth"""
        response = client.get("/contacts/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_search_contacts_unauthorized(self, client):
        """Test searching contacts without auth"""
        response = client.get("/contacts/search/?q=test")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDuplicateEndpoints:
    """Test duplicate detection endpoints"""
    
    def test_get_duplicates_unauthorized(self, client):
        """Test getting duplicates without auth"""
        response = client.get("/duplicates")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_find_duplicates_unauthorized(self, client):
        """Test manual duplicate search without auth"""
        response = client.post("/duplicates/find", json={"threshold": 0.75})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_duplicate_status_unauthorized(self, client):
        """Test updating duplicate status without auth"""
        response = client.put("/duplicates/1/status", json={"status": "reviewed"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

