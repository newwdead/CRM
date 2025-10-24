"""
Tests for Admin API endpoints (audit logs, statistics, documentation, backups)
"""
import pytest
from fastapi import status


class TestAuditLogEndpoints:
    """Test suite for /audit endpoints"""
    
    def test_get_recent_audit_logs_as_admin(self, client, admin_auth_token, db_session):
        """Test getting recent audit logs as admin"""
        response = client.get(
            "/audit/recent?limit=50",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
    
    def test_get_audit_logs_with_filter(self, client, admin_auth_token):
        """Test getting audit logs with entity_type filter"""
        response = client.get(
            "/audit/recent?entity_type=contact&limit=20",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        logs = response.json()
        assert isinstance(logs, list)
    
    def test_get_audit_logs_as_regular_user(self, client, auth_token):
        """Test that regular users cannot access audit logs"""
        response = client.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStatisticsEndpoints:
    """Test suite for /statistics endpoints"""
    
    def test_get_statistics_overview(self, client, auth_token, db_session):
        """Test getting overall statistics"""
        response = client.get(
            "/statistics/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "totals" in data
        assert "completeness" in data
        assert "top_companies" in data
        assert "top_positions" in data
        assert "contacts_by_month" in data
    
    def test_get_tag_statistics(self, client, auth_token):
        """Test getting tag statistics"""
        response = client.get(
            "/statistics/tags",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tags" in data
        assert "total_tags" in data
        assert isinstance(data["tags"], list)
    
    def test_get_group_statistics(self, client, auth_token):
        """Test getting group statistics"""
        response = client.get(
            "/statistics/groups",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "groups" in data
        assert "total_groups" in data
        assert isinstance(data["groups"], list)


class TestDocumentationEndpoints:
    """Test suite for /documentation endpoints"""
    
    def test_list_documentation_as_admin(self, client, admin_auth_token):
        """Test listing available documentation as admin"""
        response = client.get(
            "/documentation",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
    
    def test_get_specific_documentation(self, client, admin_auth_token):
        """Test getting specific documentation file"""
        # First, list docs to get a valid filename
        list_response = client.get(
            "/documentation",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        docs = list_response.json()["documents"]
        
        if len(docs) > 0:
            # Get first document
            doc_name = docs[0]["filename"]
            response = client.get(
                f"/documentation/{doc_name}",
                headers={"Authorization": f"Bearer {admin_auth_token}"}
            )
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "filename" in data
            assert "content" in data
            assert "size" in data
    
    def test_get_nonexistent_documentation(self, client, admin_auth_token):
        """Test getting non-existent documentation returns 404"""
        response = client.get(
            "/documentation/NONEXISTENT_FILE.md",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_path_traversal_protection(self, client, admin_auth_token):
        """Test that path traversal attempts are blocked"""
        response = client.get(
            "/documentation/../../../etc/passwd",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        # Path traversal should return either 400 (validation) or 404 (not found)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    
    def test_non_markdown_file_blocked(self, client, admin_auth_token):
        """Test that non-markdown files are blocked"""
        response = client.get(
            "/documentation/test.txt",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_documentation_as_regular_user(self, client, auth_token):
        """Test that regular users cannot access documentation"""
        response = client.get(
            "/documentation",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestBackupEndpoints:
    """Test suite for /backups endpoints"""
    
    def test_list_backups_as_admin(self, client, admin_auth_token):
        """Test listing backups as admin"""
        response = client.get(
            "/backups",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "backups" in data
        assert "total" in data
        assert isinstance(data["backups"], list)
    
    def test_create_backup_as_admin(self, client, admin_auth_token):
        """Test creating a backup as admin"""
        response = client.post(
            "/backups/create",
            headers={"Authorization": f"Bearer {admin_auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_backups_as_regular_user(self, client, auth_token):
        """Test that regular users cannot access backups"""
        response = client.get(
            "/backups",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

